"""
Example: Solving Cloudflare Interstitial using Solver.tr

This example demonstrates how to use the Solver.tr API to solve
Cloudflare Interstitial captchas asynchronously.

Note: Solver.tr supports Cloudflare Turnstile and Interstitial captchas.
"""
import asyncio
import logging

from playwright.async_api import async_playwright

from playwright_captcha import CaptchaType, SolverTrSolver, FrameworkType
from playwright_captcha.solvers.api.solvertr import AsyncSolverTr

logging.basicConfig(
    level='INFO',
    format='[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)


async def solve_interstitial() -> None:
    # Initialize AsyncSolverTr client with your API key
    # Get your API key from https://solver.tr
    async_solvertr = AsyncSolverTr(api_key="YOUR_API_KEY_HERE")

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()

        # Initialize the Solver.tr solver
        solver = SolverTrSolver(
            framework=FrameworkType.PLAYWRIGHT,
            page=page,
            async_solvertr_client=async_solvertr,
            max_attempts=3,
            attempt_delay=5
        )

        await solver.prepare()  # Prepare the solver (apply patches)

        # Navigate to a page with Cloudflare Interstitial
        await page.goto("https://2captcha.com/demo/cloudflare-turnstile-challenge")

        # Solve the captcha
        token = await solver.solve_captcha(
            captcha_container=page,
            captcha_type=CaptchaType.CLOUDFLARE_INTERSTITIAL
        )

        print(f"Captcha solved! Token: {token[:50]}...")

        # Optional: Check balance
        balance = await solver.get_balance()
        print(f"Solver.tr balance: ${balance}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(solve_interstitial())
