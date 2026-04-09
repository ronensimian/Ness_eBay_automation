import logging
import os
import random
import uuid
from datetime import datetime
from typing import List, Optional
from playwright.async_api import Page, Locator, expect

from config import settings

logger = logging.getLogger(__name__)

class UIActionHandler:
    """Resilient UI interaction handler."""
    
    DEFAULT_TIMEOUT = settings.DEFAULT_TIMEOUT
    RETRY_TIMEOUT = settings.UI_RETRY_TIMEOUT
    
    def __init__(self, page: Page):
        self.page = page
        self._initialized = False
        self._stealth_injected = False

    async def _inject_stealth(self):
        """Injects stealth scripts to minimize bot detection."""
        if not self._stealth_injected:
            # Mask common automation indicators
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = { runtime: {} };
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            """)
            self._stealth_injected = True

    async def _ensure_style_injected(self):
        """Standardizes highlighting style in the main page."""
        if not self._initialized:
            await self.page.add_style_tag(content="""
                [data-automated-found="true"] {
                    outline: 2px solid red !important;
                    outline-offset: -2px !important;
                    z-index: 10000 !important;
                }
            """)
            self._initialized = True

    async def check_for_captcha(self):
        """
        Detects if a CAPTCHA or 'Security Measure' page is visible.
        If found, it logs a warning and attempts automatic resolution.
        NOW RESTRICTED: Only runs if the current URL is a cart page.
        """
        current_url = self.page.url.lower()
        if "cart.ebay.com" not in current_url and "/cart" not in current_url:
            return

        captcha_indicators = [
            "text='Please verify you are a human'",
            "text='Security Check'",
            "iframe[src*='captcha']",
            "text='verify you\\'re not a robot'",
            "id='captcha-container'",
            "text='Verify it\\'s you'",
            "button:has-text('Verify')"
        ]
 
        for indicator in captcha_indicators:
            try:
                locator = await self.find_element(indicator, f"Captcha Indicator '{indicator}'", timeout=200, is_optional=True, screenshot=False, check_captcha=False)
                if locator and await locator.is_visible():
                    logger.warning(f"CAPTCHA DETECTED using indicator: {indicator}")
                    await self.highlight_element_and_capture_screenshot(locator, "Captcha Challenge")
                    
                    # Try automated solve
                    if await self.attempt_solve_captcha():
                        return

                    logger.info("Auto-solve failed or not applicable. Waiting for manual resolution (60s)...")
                    for _ in range(60):
                        if not await locator.is_visible():
                            logger.info("Captcha resolved manually! Proceeding...")
                            return
                        await self.page.wait_for_timeout(1000)
            except Exception:
                continue

    async def attempt_solve_captcha(self) -> bool:
        """Attempts to solve the captcha by clicking checkboxes or buttons."""
        try:
            # 1. Look for common 'I am human' checkboxes inside iframes (hCaptcha / ReCaptcha)
            iframes = self.page.frames
            for frame in iframes:
                try:
                    # hCaptcha / ReCaptcha specific selectors
                    checkbox_selectors = [
                        "input[type='checkbox']",
                        "#checkbox",
                        "#anchor-checkbox",
                        ".recaptcha-checkbox-border",
                        "[aria-checked='false']",
                        "div[role='checkbox']"
                    ]
                    for selector in checkbox_selectors:
                        # Use find_element with parent=frame for standardized tracking
                        checkbox = await self.find_element(selector, f"Captcha Checkbox '{selector}'", parent=frame, timeout=500, is_optional=True, screenshot=False, check_captcha=False)
                        if checkbox and await checkbox.is_visible():
                            logger.info(f"Attempting to click CAPTCHA checkbox ({selector}) in frame: {frame.name or frame.url[:30]}...")
                            
                            # Move mouse to checkbox with randomization
                            box = await checkbox.bounding_box()
                            if box:
                                x = box['x'] + box['width'] / 2 + (random.random() - 0.5) * 5
                                y = box['y'] + box['height'] / 2 + (random.random() - 0.5) * 5
                                await self.page.mouse.move(x, y, steps=10)
                                await self.page.mouse.click(x, y)
                            else:
                                await checkbox.click()
                                
                            await self.page.wait_for_timeout(3000)
                            if not await checkbox.is_visible() or await checkbox.get_attribute("aria-checked") == "true":
                                logger.info("Checkbox clicked successfully!")
                                return True
                except Exception:
                    continue

            # 2. Look for 'Verify' or 'Press and Hold' buttons (eBay proprietary)
            verify_selectors = [
                "button:has-text('Verify')",
                "#verify-button",
                ".verify-button",
                "text='Verify myself'",
                "button:has-text('Try again')"
            ]
            for selector in verify_selectors:
                verify_btn = await self.find_element(selector, f"Verify Button '{selector}'", timeout=1000, is_optional=True, screenshot=False, check_captcha=False)
                if verify_btn and await verify_btn.is_visible():
                    logger.info(f"Attempting to click Verify button ({selector})...")
                    await verify_btn.click()
                    await self.page.wait_for_timeout(3000)
                    return True
                
            return False
        except Exception as e:
            logger.debug(f"Auto-solve error: {e}")
            return False

    async def breathe(self, min_ms=100, max_ms=500):
        """Adds a slight randomized delay to mimic human reading/decision time."""
        delay = random.randint(min_ms, max_ms)
        await self.page.wait_for_timeout(delay)

    async def highlight_element_and_capture_screenshot(self, locator: Locator, name: str = "element", screenshot: bool = True):
        """Centers, highlights with a red frame, and optionally takes a screenshot."""
        try:
            # 1. Ensure style is injected in the main page
            await self._ensure_style_injected()

            # 2. Scroll into view
            await locator.scroll_into_view_if_needed()
            
            # 3. Apply Highlight (Mark with attribute for CSS-based 'painting')
            # The JS evaluate runs in the frame of the element.
            # We inject the style dynamically into whichever frame the element is in.
            await locator.evaluate("""el => {
                const styleId = 'automated-highlight-style';
                if (!document.getElementById(styleId)) {
                    const s = document.createElement('style');
                    s.id = styleId;
                    s.innerHTML = "[data-automated-found='true'] { outline: 6px solid #ff0000 !important; outline-offset: 4px !important; z-index: 9999999 !important; box-shadow: 0 0 20px 5px rgba(255, 0, 0, 0.6) !important; }";
                    document.head.appendChild(s);
                }
                el.setAttribute('data-automated-found', 'true');
                setTimeout(() => el.removeAttribute('data-automated-found'), 1000);
            }""")
            
            if screenshot:
                # 4. Capture screenshot
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                filename = f"{timestamp}.png"
                target_dir = getattr(self.page, "screenshot_dir", os.path.join("results", "screenshots"))
                os.makedirs(target_dir, exist_ok=True)
                path = os.path.join(target_dir, filename)
                
                await self.page.screenshot(path=path, full_page=False)
                logger.info(f"Visual checkpoint captured for '{name}': {path}")
                
                # Keep the highlight visible slightly longer during synchronous screenshot wait
                await self.page.wait_for_timeout(200)

        except Exception as e:
            logger.debug(f"Highlight/Screenshot skipped for '{name}': {e}")

    async def find_element(self, selectors: List[str] | str | Locator, name: str = "element", timeout: int = DEFAULT_TIMEOUT, is_optional: bool = False, screenshot: bool = True, check_captcha: bool = True, parent: Optional[Locator | Page] = None) -> Optional[Locator]:
        """Attempts to find an element using fallback selectors, optionally within a parent."""
        if isinstance(selectors, Locator):
            try:
                # Always highlight found element, even if screenshot is False
                await self.highlight_element_and_capture_screenshot(selectors, name, screenshot=screenshot)
                return selectors
            except Exception:
                if is_optional: return None
                raise

        # 2. Normalize selectors to a list
        if isinstance(selectors, str):
            selectors = [selectors]
            
        # 3. Always check for blockers before searching (unless skipped)
        if check_captcha:
            await self._inject_stealth()
            await self.check_for_captcha()
        
        # 4. Determine search root
        root = parent if parent else self.page
        
        last_error = RuntimeError(f"No selectors provided for {name}")
        total_selectors = len(selectors)
        for i, selector in enumerate(selectors):
            current_try = i + 1
            try:
                locator = root.locator(selector).first
                # Wait for the element to be visible before highlighting/returning
                current_timeout = timeout if i == 0 else self.RETRY_TIMEOUT
                await locator.wait_for(state="visible", timeout=current_timeout)
                    
                # Visual detection checkpoint - centers and highlights element
                await self.highlight_element_and_capture_screenshot(locator, name, screenshot=screenshot)
                
                logger.info(f"SUCCESS: Found '{name}' (Attempt {current_try}/{total_selectors})")
                return locator
            except Exception as e:
                if is_optional:
                    logger.debug(f"Optional element '{name}' not found on attempt {current_try}/{total_selectors}")
                else:
                    logger.warning(f"ATTEMPT {current_try}/{total_selectors} FAILED for '{name}' using: {selector}")
                last_error = e

        if is_optional:
            logger.info(f"NOTICE: Optional element '{name}' not detected after all attempts.")
            return None
            
        logger.error(f"FATAL: All selectors failed for '{name}'.")
        raise last_error

    async def click(self, selectors: List[str] | str, name: str = "element", screenshot: bool = True, check_captcha: bool = True):
        """Clicks an element with resilience and randomized offsets."""
        try:
            locator = await self.find_element(selectors, name, screenshot=screenshot, check_captcha=check_captcha)
            
            # Randomized coordinate offset to mimic human click
            box = await locator.bounding_box()
            if box:
                x = box['x'] + box['width'] * (0.3 + random.random() * 0.4)
                y = box['y'] + box['height'] * (0.3 + random.random() * 0.4)
                await self.page.mouse.click(x, y)
            else:
                await locator.click(timeout=self.RETRY_TIMEOUT)
        except Exception as e:
            logger.warning(f"Initial click failed or intercepted for '{name}': {e}. Attempting recovery/forced click.")
            locator = await self.find_element(selectors, name, screenshot=screenshot, check_captcha=check_captcha)
            await locator.click(force=True)
            
        logger.info(f"Clicked '{name}'")

    async def fill(self, selectors: List[str] | str, value: str, name: str = "element", delete_count: int = 0, screenshot: bool = True, check_captcha: bool = True):
        """Fills an input with resilience."""
        locator = await self.find_element(selectors, name, screenshot=screenshot, check_captcha=check_captcha)
        await locator.click()
        await locator.clear()
        
        if delete_count > 0:
            logger.info(f"Performing {delete_count} manual clear actions for '{name}'")
            for _ in range(delete_count):
                await self.page.keyboard.press("Delete")
                await self.page.keyboard.press("Backspace")
            await self.page.wait_for_timeout(500)   
            
        await locator.fill(value)
        logger.info(f"Filled '{name}' with value: {value}")

    async def select_option(self, selectors: List[str] | str, value: str = None, label: str = None, index: int = None, name: str = "dropdown", screenshot: bool = True, check_captcha: bool = True):
        """Selects an option from a dropdown."""
        locator = await self.find_element(selectors, name, screenshot=screenshot, check_captcha=check_captcha)
        
        # Highlight before selection
        await self.highlight_element_and_capture_screenshot(locator, f"{name} before selection", screenshot=screenshot)
        
        if value is not None:
            await locator.select_option(value=value)
        elif label is not None:
            await locator.select_option(label=label)
        elif index is not None:
            await locator.select_option(index=index)
            
        logger.info(f"Selected option in '{name}'")
        # Optional: Highlight after selection to show state
        await self.highlight_element_and_capture_screenshot(locator, f"{name} after selection", screenshot=screenshot)
