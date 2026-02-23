"""
CapMonster implementation for solving captchas.
"""
import time
import requests
import logging
from datetime import datetime
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def get_timestamp() -> str:
    """Get current timestamp for logging."""
    return datetime.now().strftime("%H:%M:%S")


class CapMonsterSolver():
    """CapMonster captcha solving service implementation."""
    
    API_BASE = "https://api.capmonster.cloud"
    
    def __init__(self, api_key: str):
        """
        Initialize CapMonster solver.
        
        Args:
            api_key: CapMonster API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def recaptcha(self, site_key: str, page_url: str, invisible: bool = False) -> str:
        """
        Solve reCAPTCHA v2 using CapMonster.
        
        Args:
            site_key: The reCAPTCHA site key
            page_url: The URL of the page with the captcha
            invisible: Whether it's an invisible reCAPTCHA
            
        Returns:
            The g-recaptcha-response token
        """
        # Create task
        task_payload = {
            "clientKey": self.api_key,
            "task": {
                "type": "RecaptchaV2Task",
                "websiteURL": page_url,
                "websiteKey": site_key
            }
        }
        
        # Add isInvisible if True
        if invisible:
            task_payload["task"]["isInvisible"] = True
        
        logger.info(f"[CapMonster] Creating task for {page_url}...")
        response = self.session.post(f"{self.API_BASE}/createTask", json=task_payload)
        result = response.json()
        
        if result.get("errorId") != 0:
            raise Exception(f"CapMonster createTask error: {result.get('errorDescription', 'Unknown error')}")
        
        task_id = result.get("taskId")
        
        logger.info(f"[CapMonster] Task created: {task_id}, polling for result...")
        
        # Poll for result
        max_attempts = 120
        for attempt in range(max_attempts):
            time.sleep(1)
            
            result_payload = {
                "clientKey": self.api_key,
                "taskId": task_id
            }
            
            response = self.session.post(f"{self.API_BASE}/getTaskResult", json=result_payload)
            result = response.json()
            
            if result.get("errorId") != 0:
                raise Exception(f"CapMonster getTaskResult error: {result.get('errorDescription', 'Unknown error')}")
            
            status = result.get("status")
            
            if status == "ready":
                solution = result.get("solution", {})
                token = solution.get("gRecaptchaResponse")
                
                # Log if userAgent is provided (should be used when submitting)
                if solution.get("userAgent"):
                    logger.info(f"[CapMonster] Note: userAgent provided in response")
                
                logger.info(f"[CapMonster] Solved in {attempt + 1}s")
                return token
            
            if attempt % 5 == 0:
                logger.info(f"[CapMonster] Still solving... ({attempt}s)")
        
        raise Exception("CapMonster timeout: captcha not solved in 120 seconds")
    
    def turnstile(self, site_key: str, page_url: str, action: str = None, cdata: str = None, pagedata: str = None) -> str:
        """
        Solve Cloudflare Turnstile using CapMonster.
        
        Args:
            site_key: The Turnstile site key (starts with 0x4)
            page_url: The URL of the page with the captcha
            action: Optional action field from callback function
            cdata: Optional data field from cData parameter
            
        Returns:
            The cf-turnstile-response token
        """
        # Create task - CapMonster uses TurnstileTask
        task_payload = {
            "clientKey": self.api_key,
            "task": {
                "type": "TurnstileTask",
                "websiteURL": page_url,
                "websiteKey": site_key
            }
        }
        
        # Add optional parameters if provided
        if action:
            task_payload["task"]["pageAction"] = action
        if cdata:
            task_payload["task"]["data"] = cdata
        if pagedata:
            task_payload["task"]["pageData"] = pagedata
        
        logger.info(f"[CapMonster] Creating Turnstile task for {page_url}...")
        response = self.session.post(f"{self.API_BASE}/createTask", json=task_payload)
        result = response.json()
        
        if result.get("errorId") != 0:
            raise Exception(f"CapMonster createTask error: {result.get('errorDescription', 'Unknown error')}")
        
        task_id = result.get("taskId")
        
        logger.info(f"[CapMonster] Turnstile task created: {task_id}, polling for result...")
        
        # Poll for result (5-20 seconds typical, max 120 seconds)
        max_attempts = 120
        for attempt in range(max_attempts):
            time.sleep(1)
            
            result_payload = {
                "clientKey": self.api_key,
                "taskId": task_id
            }
            
            response = self.session.post(f"{self.API_BASE}/getTaskResult", json=result_payload)
            result = response.json()
            
            if result.get("errorId") != 0:
                raise Exception(f"CapMonster getTaskResult error: {result.get('errorDescription', 'Unknown error')}")
            
            status = result.get("status")
            
            if status == "ready":
                solution = result.get("solution", {})
                token = solution.get("token")
                
                # Log if userAgent is provided (may be useful for some implementations)
                if solution.get("userAgent"):
                    logger.info(f"[CapMonster] Note: userAgent provided in response")
                
                logger.info(f"[CapMonster] Turnstile solved in {attempt + 1}s")
                return token
            
            if attempt % 5 == 0:
                logger.info(f"[CapMonster] Still solving Turnstile... ({attempt}s)")
        
        raise Exception("CapMonster timeout: Turnstile not solved in 120 seconds")
    
    def get_balance(self) -> float:
        """
        Get CapMonster account balance.
        
        Returns:
            Account balance in USD
        """
        payload = {
            "clientKey": self.api_key
        }
        
        response = self.session.post(f"{self.API_BASE}/getBalance", json=payload)
        result = response.json()
        
        if result.get("errorId") != 0:
            raise Exception(f"CapMonster getBalance error: {result.get('errorDescription', 'Unknown error')}")
        
        return result.get("balance", 0)