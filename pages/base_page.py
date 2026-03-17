import logging
from typing import Optional
from playwright.async_api import Page
from utils.locator_utility import UIActionHandler

class BasePage:
    """Base class for all Page Objects in the Enterprise Framework."""
    
    # Global locators
    LOGO = ["#gh-logo", "//svg[@id='gh-logo']"]
    GLOBAL_SEARCH = ["#gh-ac", "input[name='_nkw']", "//input[@id='gh-ac']"]

    def __init__(self, page: Page):
        self.page = page
        self.ui = UIActionHandler(page)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def navigate(self, url: str):
        """Navigates to a specific URL with human-like timing and blocker checks."""
        self.logger.info(f"Navigating to {url}")
        await self.ui.breathe(100, 300)
        await self.page.goto(url, wait_until="load")
        await self.ui.check_for_captcha()

    async def wait_for_ready(self, timeout: int = 5000):
        """Wait for the page to be in a stable state using both Playwright events."""
        try:
            await self.page.wait_for_load_state("load", timeout=timeout)
            # Short load as a safety net
            await self.page.wait_for_load_state("load", timeout=500)
        except Exception:
            self.logger.debug("Wait for ready timed out or data-uvcc-ready not found, proceeding...")



    @property
    async def title(self) -> str:
        return await self.page.title()
