"""
Solver.tr implementation for solving Cloudflare Turnstile.
Note: This provider only supports Turnstile, not reCAPTCHA v2.
"""
import requests
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

def get_timestamp() -> str:
    """Get current timestamp for logging."""
    return datetime.now().strftime("%H:%M:%S")


class SolverTrSolver:
    """Solver.tr captcha solving service implementation (Turnstile only)."""
    
    API_URL = "https://api.solver.tr/v1/turnstile/solve"
    
    def __init__(self, api_key: str):
        """
        Initialize Solver.tr solver.
        
        Args:
            api_key: Solver.tr API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.last_balance = None
    
    def recaptcha(self, site_key: str, page_url: str, invisible: bool = False) -> str:
        """
        Solve reCAPTCHA v2 - NOT SUPPORTED by Solver.tr.
        
        Raises:
            NotImplementedError: Solver.tr only supports Turnstile
        """
        raise NotImplementedError(
            "Solver.tr only supports Cloudflare Turnstile. "
            "Use a different provider (e.g., capmonster, capsolver) for reCAPTCHA v2."
        )
    
    def turnstile(self, site_key: str, page_url: str, action: str = None, cdata: str = None) -> str:
        """
        Solve Cloudflare Turnstile using Solver.tr.
        
        Args:
            site_key: The Turnstile site key (starts with 0x4)
            page_url: The URL of the page with the captcha
            action: Optional action parameter (not used by Solver.tr)
            cdata: Optional cdata parameter (not used by Solver.tr)
            
        Returns:
            The cf-turnstile-response token
        """
        params = {
            "url": page_url,
            "sitekey": site_key,
            "apikey": self.api_key
        }
        
        logger.info(f"[Solver.tr] Solving Turnstile for {page_url}...")
        
        try:
            response = self.session.get(self.API_URL, params=params, timeout=120)
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
            
            data = response.json()
            
            if data.get("success"):
                token = data.get("token")
                self.last_balance = data.get("balance")
                
                # Replaced print with logger.info
                logger.info(f"[Solver.tr] Turnstile solved! (Balance: {self.last_balance})")
                return token
            else:
                error = data.get("error") or data.get("message") or str(data)
                raise Exception(f"Solver.tr error: {error}")
                
        except requests.Timeout:
            raise Exception("Solver.tr timeout: request took too long")
        except requests.RequestException as e:
            raise Exception(f"Solver.tr request error: {e}")
    
    def get_balance(self) -> float:
        """
        Get Solver.tr account balance.
        
        Returns:
            Account balance (cached from last solve, or 0 if not available)
        """
        # Solver.tr returns balance with each solve request
        # We cache it from the last solve
        if self.last_balance is not None:
            try:
                return float(self.last_balance)
            except (ValueError, TypeError):
                pass
        return 0.0