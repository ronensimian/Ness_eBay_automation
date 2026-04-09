import re
import logging
import allure
from pages.base_page import BasePage

logger = logging.getLogger(__name__)

class CartPage(BasePage):
    """eBay Cart Page Object."""
    
    CART_TOTAL = [
        "div[data-test-id='SUBTOTAL']",
        "//div[@data-test-id='SUBTOTAL']",
        ".cart-summary-line-item__value",
        ".app-cart-summary__total-value",
        "[class*='subtotal']",
        "//span[contains(text(), 'Subtotal')]/following::span[1]"
    ]

    CART_ITEM_COUNT = [
        # Primary: Order Summary panel — matches "Item(1)" or "Items(3)"
        "div[data-test-id='cart-summary'] .cart-summary-line-item:first-child",
        # Fallback: any span whose text starts with "Item"
        "div[data-test-id='ITEM_TOTAL']",
        "//div[@data-test-id='cart-summary']//span[starts-with(normalize-space(.), 'Item')]",
        # Last resort: cart icon badge in the header
        "#gh-cart-n",
        ".gh-cart-n"
    ]

    async def get_item_count(self) -> int:
        """Extracts the number of items from the Order Summary panel.
        Handles formats: 'Item (1)', 'Items (3)'
        """
        try:
            locator = await self.ui.find_element(
                self.CART_ITEM_COUNT, "Cart Item Count", timeout=5000, is_optional=True
            )
            text = await locator.inner_text()
            self.logger.info(f"Cart count raw text: '{text}'")
            # Match number inside parentheses: "Item (1)" -> 1, "Items (3)" -> 3
            match = re.search(r'Items?\s*\((\d+)\)', text, re.IGNORECASE)
            if match:
                count = int(match.group(1))
                self.logger.info(f"Detected {count} item(s) in cart from Order Summary.")
                return count
            # Fallback: any standalone number (e.g. header badge "3")
            match = re.search(r'(\d+)', text)
            if match:
                count = int(match.group(1))
                self.logger.info(f"Detected {count} item(s) in cart via fallback number.")
                return count
        except Exception as e:
            self.logger.warning(f"Could not detect item count in cart: {e}")
        return 0

    async def get_cart_total(self) -> float:
        """Extracts the numeric subtotal from the cart page."""
        locator = await self.ui.find_element(self.CART_TOTAL, "Cart Total Subtotal")
        total_text = await locator.inner_text()
        
        # Robust extraction using regex
        match = re.search(r'[\d,.]+', total_text.replace(',', ''))
        if not match:
            self.logger.error(f"Could not parse cart total from text: {total_text}")
            return 0.0
            
        total_val = float(match.group().replace(',', ''))
        self.logger.info(f"Extracted cart total: {total_val}")
        return total_val

    @allure.step("Final Verification: Check if cart has {items_count} items and total is within budget")
    async def verify_cart_constraints(self, budget_per_item: float, items_count: int) -> None:
        """
        Verifies the shopping cart amount and exact item count.
        """
        # 1. Open the shopping cart
        await self.navigate("https://cart.ebay.com")
        await self.wait_for_ready()

        # 2. Verify exact item count
        actual_count = await self.get_item_count()
        if actual_count != items_count:
            self.logger.error(f"ITEM COUNT MISMATCH: Expected {items_count}, but found {actual_count}")
            raise AssertionError(f"EXACT ITEM COUNT MISMATCH: Expected precisely {items_count} items, but found {actual_count} in the cart.")
        
        # 3. Read the total amount
        total = await self.get_cart_total()

        # 4. Calculate threshold
        threshold = items_count * budget_per_item
        
        self.logger.info(f"Cart Verification: Total={total}, Threshold={threshold} ({items_count} items * ILS {budget_per_item})")
        
        # 5. Verify total
        if total > threshold:
            raise AssertionError(f"Cart total {total} exceeds the calculated threshold of {threshold}")
            
        self.logger.info("Verification Success: Cart matches expected constraints.")
