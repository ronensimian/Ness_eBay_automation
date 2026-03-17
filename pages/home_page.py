from pages.base_page import BasePage

class HomePage(BasePage):
    """eBay Home Page Object."""
    
    SEARCH_INPUT = ["#gh-ac", "input[name='_nkw']", "//input[@type='text']"]
    SEARCH_BUTTON = ["#gh-search-btn", "button#gh-search-btn", "input#gh-search-btn", "//button[@id='gh-search-btn']"]
    CATEGORY_SELECT = ["#gh-cat", "select[aria-label='Select a category for search']", "//select[@id='gh-cat']"]
    CART_ICON = [".gh-cart", "a.gh-flyout__target[href*='cart.ebay.com']", "//a[contains(@class, 'gh-cart')]"]

    async def search_for_product(self, query: str):
        """Executes a search for the given product query."""
        self.logger.info(f"Searching for product: {query}")
        await self.ui.fill(self.SEARCH_INPUT, query, "Search Input")
        await self.ui.click(self.SEARCH_BUTTON, "Search Button")
        await self.wait_for_ready()
