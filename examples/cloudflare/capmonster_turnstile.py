"""
Example: Solving Cloudflare Turnstile using CapMonster

This example demonstrates how to use the CapMonster API to solve
Cloudflare Turnstile captchas asynchronously.
"""
import asyncio
import logging

from playwright.async_api import async_playwright

from playwright_captcha import CaptchaType, CapMonsterSolver, FrameworkType
from playwright_captcha.solvers.api.capmonster import AsyncCapMonster

logging.basicConfig(
    level='INFO',
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)


async def solve_turnstile() -> None:
    # Initialize AsyncCapMonster client with your API key
    # Get your API key from https://capmonster.cloud
    async_capmonster = AsyncCapMonster(api_key="YOUR_API_KEY_HERE")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()

        # Initialize the CapMonster solver
        solver = CapMonsterSolver(
            framework=FrameworkType.PLAYWRIGHT,
            page=page,
            async_capmonster_client=async_capmonster,
            max_attempts=3,
            attempt_delay=5
        )

        await solver.prepare()  # Prepare the solver (apply patches)

        # Navigate to a page with Cloudflare Turnstile
        await page.goto("https://2captcha.com/demo/cloudflare-turnstile-challenge")

        # Solve the captcha
        token = await solver.solve_captcha(
            captcha_container=page,
            captcha_type=CaptchaType.CLOUDFLARE_TURNSTILE
        )

        print(f"Captcha solved! Token: {token[:50]}...")

        # Optional: Check balance
        balance = await solver.get_balance()
        print(f"CapMonster balance: ${balance}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(solve_turnstile())
