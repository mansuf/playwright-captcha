"""
Async client for Solver.tr captcha solving service.
Note: This provider only supports Turnstile, not reCAPTCHA v2.
"""
import logging
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


class AsyncSolverTr:
    """Async client for Solver.tr captcha solving service (Turnstile only)."""

    API_URL = "https://api.solver.tr/v1/turnstile/solve"

    def __init__(self, api_key: str, session: Optional[aiohttp.ClientSession] = None):
        """
        Initialize Async Solver.tr client.

        Args:
            api_key: Solver.tr API key
            session: Optional aiohttp ClientSession to reuse
        """
        self.api_key = api_key
        self._session = session
        self._owns_session = False
        self.last_balance = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self._owns_session = True
        return self._session

    async def close(self):
        """Close the session if we own it."""
        if self._owns_session and self._session and not self._session.closed:
            await self._session.close()

    async def turnstile(self, sitekey: str, url: str, action: Optional[str] = None,
                        cdata: Optional[str] = None) -> dict:
        """
        Solve Cloudflare Turnstile using Solver.tr.

        Args:
            sitekey: The Turnstile site key (starts with 0x4)
            url: The URL of the page with the captcha
            action: Optional action parameter (not used by Solver.tr)
            cdata: Optional cdata parameter (not used by Solver.tr)

        Returns:
            dict with 'code' (token) and 'balance' keys

        Raises:
            Exception: If the request fails or returns an error
        """
        params = {
            "url": url,
            "sitekey": sitekey,
            "apikey": self.api_key
        }

        logger.info(f"[Solver.tr] Solving Turnstile for {url}...")

        try:
            session = await self._get_session()
            async with session.get(self.API_URL, params=params, timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(f"HTTP {response.status}: {text}")

                data = await response.json()

                if data.get("success"):
                    token = data.get("token")
                    self.last_balance = data.get("balance")

                    logger.info(f"[Solver.tr] Turnstile solved! (Balance: {self.last_balance})")
                    return {
                        "code": token,
                        "balance": self.last_balance
                    }
                else:
                    error = data.get("error") or data.get("message") or str(data)
                    raise Exception(f"Solver.tr error: {error}")

        except aiohttp.ClientTimeout:
            raise Exception("Solver.tr timeout: request took too long")
        except aiohttp.ClientError as e:
            raise Exception(f"Solver.tr request error: {e}")

    async def balance(self) -> dict:
        """
        Get Solver.tr account balance.

        Note: Solver.tr returns balance with each solve request.
        This method returns the cached balance from the last solve.

        Returns:
            dict with 'balance' key
        """
        balance = 0.0
        if self.last_balance is not None:
            try:
                balance = float(self.last_balance)
            except (ValueError, TypeError):
                pass

        return {"balance": balance}
