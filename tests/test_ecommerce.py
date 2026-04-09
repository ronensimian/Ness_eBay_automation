import pytest
import logging
import allure
from typing import List
from pages.home_page import HomePage
from pages.search_results_page import SearchResultsPage
from pages.product_page import ProductPage
from pages.cart_page import CartPage
from utils.data_reader import DataReader

logger = logging.getLogger(__name__)

# Load scenarios once for parametrization
scenarios = DataReader.read_json("test_data.json")

@allure.feature("eBay eCommerce Flows")
class TestECommerceWorkflow:
    """
    Enterprise-grade test suite for eBay eCommerce flows.
    """

    @allure.step("Discovery Phase: Search and apply price filters")
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

    @pytest.mark.asyncio
    @allure.story("Budget-Based Shopping Flow")
    @allure.description("Verifies that a guest user can search for items within a budget and add them to the cart.")
    async def test_ebay_budget_flow(self, page_context, browser_config, scenario):
        """
        Scenario: Search for items within a budget, add to cart, and verify total.
        1. Search & Filter products.
        2. Add products to cart.
        3. Verify total subtotal aligns with budget.
        """
        allure.dynamic.title(f"Scenario: {scenario['test_name']}")
        logger.info(f"Starting Scenario: {scenario['test_name']}")
        
        with allure.step("Step 1: Discover products based on search and budget"):
            urls = await self._search_and_filter_items(page_context, scenario)
            assert urls, f"No products found for '{scenario['search_query']}' within the specified price range."
        
        with allure.step("Step 2: Add discovered products to the shopping cart"):
            product_page = ProductPage(page_context)
            await product_page.add_items_to_cart(urls)
        
        with allure.step("Step 3: Verify cart constraints (Item count & Total price)"):
            cart = CartPage(page_context)
            await cart.verify_cart_constraints(scenario["budget_per_item"], scenario["item_limit"])