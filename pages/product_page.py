import random
import logging
import allure
from pages.base_page import BasePage

logger = logging.getLogger(__name__)

class ProductPage(BasePage):
    """eBay Product Detail Page Object."""
    
    ADD_TO_CART = [
        "text='Add to cart'", 
        "a:has-text('Add to cart')",
        "internal:role=button[name=/add to cart/i]"
    ]
    ADD_TO_CART_CONFIRMED = [
        "//span[contains(text(), 'Added to cart')]",
        "//h2[contains(text(), 'Added to cart')]",
        ".header-title:has-text('Added to cart')"
    ]
    SEE_IN_CART = [
        "a[data-testid='ux-call-to-action'] span:has-text('See in cart')", 
        "//a[contains(., 'See in cart')]"
    ]
    VARIANTS = [
        "button[value='Select']", 
        # need to avoid the Ratings dropdown: value="All ratings"
        "select.x-msku__select-box",
        ".x-msku__select-box",
        "select[id*='msku']",
        "select[aria-label*='selection']"
    ]
    DROPDOWN_OPTIONS = [
        "[data-testid='x-price-section'] ~ select.x-msku__select-box",
        "select.x-msku__select-box",
        "select[id*='msku']"
    ]
    SWATCH_OPTIONS = [
        "[data-testid='x-msku-evo'] div[role='button']:not([aria-disabled='true'])",
        ".x-msku__swatch-item:not(.x-msku__swatch-item--disabled)",
        "div.grid-swatch input + label",
        "ul.swatches-list li:not(.disabled) button"
    ]

    @allure.step("Select all required product variants (Size, Color, etc.)")
    async def select_required_variants(self):
        """Standardizes variant selection logic for standard selects, custom listboxes, and swatches."""
        self.logger.info("Scanning for required product variants...")
        
        # 1. Handle standard Select dropdowns
        for base_sel in self.DROPDOWN_OPTIONS:
            if await self.page.locator(base_sel).count() == 0:
                continue

            for i in range(5):
                try:
                    # Use the locator directly with .nth() instead of string-based :nth-match
                    # This is much safer and avoids "CSS.escape" errors
                    sel_locator = self.page.locator(base_sel).nth(i)
                    if not await sel_locator.is_visible(timeout=500):
                        break
                    
                    option_selector = "option:not([value='-1']):not(:has-text('Select')):not(:has-text('Choose')):not(:has-text('Out of stock'))"
                    options_root = sel_locator.locator(option_selector)
                    valid_options_count = await options_root.count()
                    
                    if valid_options_count > 0:
                        current_val = await sel_locator.evaluate("el => el.value")
                        if current_val in ["-1", ""] or "select" in (await sel_locator.evaluate("el => el.options[el.selectedIndex].text")).lower():
                            target_idx = random.randint(0, valid_options_count - 1)
                            target_opt = options_root.nth(target_idx)
                            target_val = await target_opt.get_attribute("value")
                            await sel_locator.select_option(value=target_val)
                            await self.page.wait_for_timeout(300)
                except Exception as e:
                    self.logger.debug(f"Dropdown variation skip: {e}")
                    continue

        # 2. Handle Custom Evo Listboxes (Buttons that open menus)
        for base_sel in self.VARIANTS:
            if "select" in base_sel.lower(): continue
            
            if await self.page.locator(base_sel).count() == 0:
                continue

            for i in range(5):
                try:
                    btn = self.page.locator(base_sel).nth(i)
                    if not await btn.is_visible(timeout=500):
                        break
                    
                    btn_text = (await btn.inner_text()).lower()
                    unselected_patterns = ["select", "choose", "- none -", "selection"]
                    if any(p in btn_text for p in unselected_patterns):
                        self.logger.info(f"Opening listbox {i+1} ('{btn_text.strip()}')")
                        await btn.click()
                        
                        listbox_id = await btn.get_attribute("aria-controls")
                        potential_listboxes = []
                        if listbox_id: 
                            # Use attribute selector to avoid colon-escaping issues in IDs like s0-1-2:item
                            potential_listboxes.append(f"[id='{listbox_id}']")
                        potential_listboxes.extend([".listbox__options", "[role='listbox']", ".msku-sel"])
                        
                        # Find the actual active listbox using an OR selector for speed
                        active_listbox = self.page.locator(", ".join(potential_listboxes)).first
                        if not await active_listbox.is_visible(timeout=1000):
                            continue
                             
                        opt_selector = ".listbox__option:not(:has-text('Select')):not(:has-text('Choose')):not(:has-text('Out of stock'))"
                        options_locator = active_listbox.locator(opt_selector)
                        
                        count = await options_locator.count()
                        if count > 0:
                            target_idx = random.randint(0, count - 1)
                            target_opt = options_locator.nth(target_idx)
                            val_text = await target_opt.inner_text()
                            await target_opt.click()
                            await self.page.wait_for_timeout(500)
                except Exception as e:
                    self.logger.debug(f"Listbox variation skip: {e}")
                    continue

        # 3. Handle Swatches/Buttons (Grid layouts)
        for base_sel in self.SWATCH_OPTIONS:
            try:
                swatch_locator = self.page.locator(base_sel)
                count = await swatch_locator.count()
                if count > 0:
                    # Check if any are already selected
                    selected_root = await self.ui.find_element(f"{base_sel}[aria-checked='true'], {base_sel}.selected", "Selected Swatches", timeout=200, is_optional=True, screenshot=False)
                    if not selected_root or await selected_root.count() == 0:
                        target_idx = random.randint(0, count - 1)
                        target_swatch = await self.ui.find_element(swatch_locator.nth(target_idx), f"Target Swatch {target_idx + 1}")
                        await self.ui.click(target_swatch, f"Swatch {target_idx + 1}")
                        await self.page.wait_for_timeout(500)
            except Exception:
                continue
        
        # Cleanup
        await self.page.keyboard.press("Escape")
        await self.page.wait_for_timeout(300)

    @allure.step("Add current item to cart")
    async def add_to_cart(self):
        """Orchestrates selecting variants, adding to cart, and verifying success."""
        await self.page.bring_to_front()
        await self.wait_for_ready()

        # Check if already in cart
        for selector in self.SEE_IN_CART:
            try:
                see_in_cart_locator = await self.ui.find_element(selector, f"Already in Cart Indicator ({selector})", timeout=1000, is_optional=True)
                if see_in_cart_locator:
                    self.logger.info("Item already in cart based on UI indicator. Skipping addition.")
                    return True # Treat as success since it's already there
            except Exception:
                pass

        # eBay sometimes requires multiple attempts if variants don't register
        for attempt in range(2):
            await self.select_required_variants()
            self.logger.info(f"Adding item to cart (Attempt {attempt+1})")
            await self.ui.click(self.ADD_TO_CART, "Add to Cart Button")
            
            # Verify success
            try:
                confirmation = await self.ui.find_element(self.ADD_TO_CART_CONFIRMED, "Confirmation", timeout=8000)
                text = (await confirmation.inner_text()).lower()
                if "added" in text or "cart" in text:
                    self.logger.info("Verification Success: Item added to cart.")
                    return True
            except Exception:
                self.logger.warning(f"Could not verify 'Added to cart' message on attempt {attempt+1}.")
                # If it's the first attempt, try to escape and retry
                await self.page.keyboard.press("Escape")
                await self.page.wait_for_timeout(1000)
        
        return False

    @allure.step("Batch process items into cart: {urls}")
    async def add_items_to_cart(self, urls: list[str]) -> None:
        """
        Orchestrates adding multiple items to cart sequentially in the same tab.
        This ensures session/cookie persistence for guest users.
        """
        for url in urls:
            clean_url = url.split('?')[0]
            self.logger.info(f"Opening item page: {clean_url}")
            
            try:
                # 1. Navigate to the item page in the SAME tab
                # This ensures cookies/session storage are updated correctly on a single thread
                await self.page.goto(clean_url, wait_until="load")
                
                # 2. Interact with Product Page
                if not await self.add_to_cart():
                    raise Exception(f"Failed to confirm item was added to cart: {clean_url}")
                
                # 3. Synchronize Session: Wait for network to stabilize 
                # to ensure cookies/session-storage are flushed to disk
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    self.logger.debug("Network did not reach idle state, continuing anyway.")
                await self.page.wait_for_timeout(2000) 
                
                # 4. Informational log
                self.logger.info(f"Successfully added to cart and synced session for: {clean_url}")
                
            except Exception as e:
                self.logger.error(f"Failed to process item {clean_url}: {e}")
                continue
