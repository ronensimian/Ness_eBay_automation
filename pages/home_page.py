import logging
import allure
from pages.base_page import BasePage

logger = logging.getLogger(__name__)

class HomePage(BasePage):
    """eBay Home Page Object."""
    
    # HomePage-specific sections can stay here
    CATEGORY_SELECT = ["#gh-cat", "select[aria-label='Select a category for search']", "//select[@id='gh-cat']"]

    @allure.step("Navigate to eBay home page")
    async def navigate_home(self):
        from config import settings
        await self.navigate(settings.BASE_URL)
