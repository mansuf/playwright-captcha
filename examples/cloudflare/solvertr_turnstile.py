"""
Example: Solving Cloudflare Turnstile using Solver.tr

This example demonstrates how to use the Solver.tr API to solve
Cloudflare Turnstile captchas asynchronously.

Note: Solver.tr only supports Turnstile, not reCAPTCHA v2.
"""
import asyncio
from playwright.async_api import async_playwright
from playwright_captcha import SolverTrSolver, CaptchaType, FrameworkType
from playwright_captcha.solvers.api.solvertr import AsyncSolverTr


async def main():
    # Initialize AsyncSolverTr client with your API key
    # Get your API key from https://solver.tr
    async_solvertr = AsyncSolverTr(api_key="YOUR_SOLVERTR_API_KEY")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
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

        # Navigate to a page with Cloudflare Turnstile
        await page.goto("https://turnstile.page")

        # Solve the captcha
        token = await solver.solve_captcha(
            captcha_container=page,
            captcha_type=CaptchaType.CLOUDFLARE_TURNSTILE
        )

        print(f"Captcha solved! Token: {token[:50]}...")

        # Optional: Check balance
        balance = await solver.get_balance()
        print(f"Solver.tr balance: ${balance}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
