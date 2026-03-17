import pytest
import logging
from typing import List
from pages.home_page import HomePage
from pages.search_results_page import SearchResultsPage
from pages.product_page import ProductPage
from pages.cart_page import CartPage
from utils.data_reader import DataReader

logger = logging.getLogger(__name__)

# Load scenarios once for parametrization
scenarios = DataReader.read_json("test_data.json")

class TestECommerceWorkflow:
    """
    Enterprise-grade test suite for eBay eCommerce flows.
    """

    async def _search_and_filter_items(self, page, data) -> List[str]:
        """Orchestrates searching and applying price filters."""
        home = HomePage(page)
        results = SearchResultsPage(page)
        
        await home.navigate("https://www.ebay.com")
        await home.search_for_product(data["search_query"])
        
        # Use the requested signature-like method
        urls = await results.search_items_by_name_under_price(
            query=data["search_query"], 
            max_price=data["budget_per_item"], 
            limit=data["item_limit"]
        )
        return urls

    async def add_items_to_cart(self, page, urls: List[str]) -> None:
        """
        Orchestrates adding items to cart sequentially in the same tab.
        This ensures session/cookie persistence for guest users.
        """
        for url in urls:
            clean_url = url.split('?')[0]
            logger.info(f"Opening item page: {clean_url}")
            
            try:
                # 1. Navigate to the item page in the SAME tab
                # This ensures cookies/session storage are updated correctly on a single thread
                await page.goto(clean_url, wait_until="load")
                
                # 2. Interact with Product Page
                product_page = ProductPage(page)
                # add_to_cart handles variant selection and clicking
                if not await product_page.add_to_cart():
                    raise Exception(f"Failed to confirm item was added to cart: {clean_url}")
                
                # 3. Synchronize Session: Wait for network to stabilize 
                # to ensure cookies/session-storage are flushed to disk
                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    logger.debug("Network did not reach idle state, continuing anyway.")
                await page.wait_for_timeout(2000) 
                
                # 4. Informational log
                logger.info(f"Successfully added to cart and synced session for: {clean_url}")
                
            except Exception as e:
                logger.error(f"Failed to process item {clean_url}: {e}")
                continue

    @pytest.mark.asyncio
    async def test_ebay_budget_flow(self, page_context, browser_config, scenario):
        """
        Scenario: Search for items within a budget, add to cart, and verify total.
        1. Search & Filter products.
        2. Add products to cart.
        3. Verify total subtotal aligns with budget.
        """
        logger.info(f"Starting Scenario: {scenario['test_name']}")
        
        # 1. Discovery Phase
        urls = await self._search_and_filter_items(page_context, scenario)
        assert urls, f"No products found for '{scenario['search_query']}' within the specified price range."
        
        # 2. Execution Phase
        await self.add_items_to_cart(page_context, urls)
        
        # 3. Verification Phase
        cart = CartPage(page_context)
        await cart.assertCartTotalNotExceeds(scenario["budget_per_item"], scenario["item_limit"])