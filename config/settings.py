import os
from pathlib import Path

# Project Roots
ROOT_DIR = Path(__file__).parent.parent
RESULTS_DIR = ROOT_DIR / "results"
DATA_DIR = ROOT_DIR / "data"

# URLs
BASE_URL = "https://www.ebay.com"
CART_URL = "https://cart.ebay.com"

# Timeouts (ms)
DEFAULT_TIMEOUT = 5000
UI_RETRY_TIMEOUT = 1000
CAPTCHA_WAIT_TIMEOUT = 60000

# Browser Settings
IS_HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
