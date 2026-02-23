"""
Async client for CapMonster captcha solving service.
"""
import asyncio
import logging
import json
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)

def load_json(data):
    return json.loads(data)

class AsyncCapMonster:
    """Async client for CapMonster captcha solving service."""

    API_BASE = "https://api.capmonster.cloud"

    def __init__(self, api_key: str, session: Optional[aiohttp.ClientSession] = None):
        """
        Initialize Async CapMonster client.

        Args:
            api_key: CapMonster API key
            session: Optional aiohttp ClientSession to reuse
        """
        self.api_key = api_key
        self._session = session
        self._owns_session = False

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

    async def _create_task(self, task_data: dict) -> str:
        """
        Create a captcha solving task.

        Args:
            task_data: Task payload dictionary

        Returns:
            Task ID string
        """
        payload = {
            "clientKey": self.api_key,
            "task": task_data
        }

        session = await self._get_session()
        async with session.post(f"{self.API_BASE}/createTask", json=payload) as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"HTTP {response.status}: {text}")

            result = load_json(await response.text())

            if result.get("errorId") != 0:
                raise Exception(f"CapMonster createTask error: {result.get('errorDescription', 'Unknown error')}")

            task_id = result.get("taskId")
            logger.info(f"[CapMonster] Task created: {task_id}")
            return task_id

    async def _get_task_result(self, task_id: str) -> dict:
        """
        Get task result.

        Args:
            task_id: The task ID to check

        Returns:
            Result dictionary with status and solution
        """
        payload = {
            "clientKey": self.api_key,
            "taskId": task_id
        }

        session = await self._get_session()
        async with session.post(f"{self.API_BASE}/getTaskResult", json=payload) as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"HTTP {response.status}: {text}")

            result = load_json(await response.text())

            if result.get("errorId") != 0:
                raise Exception(f"CapMonster getTaskResult error: {result.get('errorDescription', 'Unknown error')}")

            return result

    async def _poll_for_result(self, task_id: str, timeout: int = 120) -> dict:
        """
        Poll for task result until ready or timeout.

        Args:
            task_id: The task ID to poll
            timeout: Maximum time to wait in seconds

        Returns:
            Solution dictionary
        """
        max_attempts = timeout
        for attempt in range(max_attempts):
            await asyncio.sleep(1)

            result = await self._get_task_result(task_id)
            status = result.get("status")

            if status == "ready":
                return result.get("solution", {})

            if attempt % 5 == 0:
                logger.info(f"[CapMonster] Still solving... ({attempt}s)")

        raise Exception(f"CapMonster timeout: captcha not solved in {timeout} seconds")

    async def recaptcha(self, sitekey: str, url: str, invisible: bool = False,
                        action: Optional[str] = None, pagedata: Optional[str] = None) -> dict:
        """
        Solve reCAPTCHA v2 using CapMonster.

        Args:
            sitekey: The reCAPTCHA site key
            url: The URL of the page with the captcha
            invisible: Whether it's an invisible reCAPTCHA
            action: Optional action parameter
            pagedata: Optional pagedata parameter

        Returns:
            dict with 'code' (token) and optional 'userAgent' keys
        """
        task_data = {
            "type": "RecaptchaV2Task",
            "websiteURL": url,
            "websiteKey": sitekey
        }

        if invisible:
            task_data["isInvisible"] = True
        if action:
            task_data["action"] = action
        if pagedata:
            task_data["pageData"] = pagedata

        logger.info(f"[CapMonster] Creating reCAPTCHA task for {url}...")

        task_id = await self._create_task(task_data)
        solution = await self._poll_for_result(task_id)

        token = solution.get("gRecaptchaResponse")
        logger.info(f"[CapMonster] reCAPTCHA solved!")

        result = {"code": token}
        if solution.get("userAgent"):
            result["userAgent"] = solution["userAgent"]

        return result

    async def turnstile(self, sitekey: str, url: str, action: Optional[str] = None,
                        data: Optional[str] = None, pagedata: Optional[str] = None, useragent: Optional[str] = None) -> dict:
        """
        Solve Cloudflare Turnstile using CapMonster.

        Args:
            sitekey: The Turnstile site key (starts with 0x4)
            url: The URL of the page with the captcha
            action: Optional action field from callback function
            data: Optional data field from cData parameter
            pagedata: Optional pageData parameter

        Returns:
            dict with 'code' (token) and optional 'userAgent' keys
        """
        task_data = {
            "type": "TurnstileTask",
            "websiteURL": url,
            "websiteKey": sitekey
        }

        if action:
            task_data["pageAction"] = action
        if data:
            task_data["data"] = data
        if pagedata:
            task_data["pageData"] = pagedata
        if useragent:
            task_data["userAgent"] = useragent

        logger.info(f"[CapMonster] Creating Turnstile task for {url}...")

        task_id = await self._create_task(task_data)
        solution = await self._poll_for_result(task_id)

        token = solution.get("token")
        logger.info(f"[CapMonster] Turnstile solved!")

        result = {"code": token}
        if solution.get("userAgent"):
            result["userAgent"] = solution["userAgent"]

        return result

    async def balance(self) -> dict:
        """
        Get CapMonster account balance.

        Returns:
            dict with 'balance' key
        """
        payload = {
            "clientKey": self.api_key
        }

        session = await self._get_session()
        async with session.post(f"{self.API_BASE}/getBalance", json=payload) as response:
            if response.status != 200:
                text = await response.text()
                raise Exception(f"HTTP {response.status}: {text}")

            result = load_json(await response.text())

            if result.get("errorId") != 0:
                raise Exception(f"CapMonster getBalance error: {result.get('errorDescription', 'Unknown error')}")

            balance = result.get("balance", 0)
            return {"balance": balance}
