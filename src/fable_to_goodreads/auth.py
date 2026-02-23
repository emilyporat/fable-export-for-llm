import asyncio
import json
from typing import Optional, Tuple
from playwright.async_api import async_playwright, Request, Response


async def fetch_credentials_via_browser(email: str, password: str) -> Tuple[str, str]:
    """
    Log into fable.co in a headless browser and intercept the auth token
    and user ID from outgoing API requests.
    """
    user_id: Optional[str] = None
    auth_token: Optional[str] = None
    got_credentials = asyncio.Event()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        async def handle_response(response: Response):
            nonlocal user_id, auth_token
            if "api.fable.co/api/settings/profile" not in response.url:
                return
            auth_header = response.request.headers.get("authorization", "")
            if not auth_header.startswith("JWT "):
                return
            try:
                data = await response.json()
                uid = data.get("id")
                if uid and not user_id:
                    user_id = uid
                    auth_token = auth_header
                    got_credentials.set()
            except Exception:
                pass

        page.on("response", handle_response)

        await page.goto("https://fable.co/signin", wait_until="networkidle")
        await page.fill("input[type='email']", email)
        await page.fill("input[type='password']", password)
        await page.keyboard.press("Enter")

        # Wait for redirect to store after login
        await page.wait_for_url("**/store", timeout=15000)

        # Navigate to library to trigger authenticated API calls
        await page.goto("https://fable.co/library", wait_until="networkidle")

        # Wait for the profile response to be intercepted
        try:
            await asyncio.wait_for(got_credentials.wait(), timeout=15)
        except asyncio.TimeoutError:
            await browser.close()
            raise RuntimeError(
                "Logged in but couldn't capture API credentials from profile response."
            )

        await browser.close()

    if not user_id or not auth_token:
        raise RuntimeError("Could not extract user ID or auth token from browser session.")

    return user_id, auth_token
