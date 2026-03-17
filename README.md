# 🛒 eCommerce Automation Framework
### *Resilient, Data-Driven, and Scalable E2E Testing with Python & Playwright*

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/playwright-v1.4x-green.svg)](https://playwright.dev/python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🌟 Overview

This enterprise-grade test automation framework is designed to handle the complexities of modern eCommerce platforms like **eBay**. Built on the **Page Object Model (POM)** and powered by **Playwright**, it offers unparalleled resilience against flaky UI elements and dynamic content.

### Key Highlights:
- **🛡️ Resilient Locator Strategy**: Multi-layer fallback mechanism (`UIActionHandler`) with automatic visual checkpoints.
- **🚀 High-Performance Parallelism**: Native support for `pytest-xdist` (optimized for up to 12 workers) to significantly reduce execution time.
- **📸 Visual Evidence**: Automatic screenshot capture with element highlighting (red framing) for every critical interaction.
- **📂 Scenario-Specific Artifacts**: Organized directory structure where logs and screenshots are isolated per test scenario.
- **🧪 Data-Driven Testing**: Scenarios are fully configurable via `test_data.json`, supporting multiple products and budget thresholds.
- **🛠️ Smart Variant Handling**: Intelligent selection of product variants (size, color, etc.) using dynamic identification of active listboxes and dropdowns.

---

## 🚀 Getting Started

### 1. Environment Setup
The framework requires **Python 3.14+**.

#### **Windows (PowerShell)**
```powershell
# 1. Create and activate virtual environment
python -m venv venv_314
.\venv_314\Scripts\Activate.ps1

# 2. Install dependencies
pip install . playwright-stealth

# 3. Install browser binaries
playwright install chromium
```

### 2. Running Tests
The framework is pre-configured for **data-driven parallel execution**.

```bash
# Run all scenarios in parallel (Headless by default)
pytest

# Run with visible browser (Headed)
$env:HEADLESS="false"; pytest

# Run with detailed real-time logs
pytest -s
```

### 🌍 Browser Support Matrix
Run tests across different browser profiles defined in `data/browser_profiles.yaml`. Passing the `--browser-profiles` flag allows you to customize the execution matrix.

| Profile Name | Browser Engine | Channel/Flavor | Target Platform |
| :--- | :--- | :--- | :--- |
| `chrome_latest` | Chromium | Google Chrome | Windows/Any |
| `firefox_latest` | Firefox | Standard | Cross-browser |
| `edge_latest` | Chromium | Microsoft Edge | Enterprise Standard |

---

## 🏗️ Architecture & Core Features

### 🧩 Page Object Model (POM)
The framework encapsulates page-specific logic within dedicated classes in the `pages/` directory.

### 🛡️ Resilient `UIActionHandler`
Located in `utils/locator_utility.py`, this utility provides:
- **Fallback Chains**: Multiple selectors for a single element to bypass DOM changes.
- **Visual Detection**: Automatic red framing and screenshot capture for every successful interaction.
- **Anti-Bot Handling**: Integrated `playwright-stealth` and manual challenge detection.

### 📸 Automated Artifact Management
At the start of every session (`pytest_sessionstart`), the framework automatically wipes previous results to ensure a clean state.

Every test run generates a structured `results/` directory:
- **`results/[Scenario_Name]/`**: Dedicated folder per test.
  - **`test.log`**: Isolated logs for that specific scenario.
  - **`screenshots/`**: High-resolution screenshots named by pure timestamp (e.g., `20260317150921907196.png`).
- **`report.html`**: A consolidated, interactive HTML dashboard for the entire session.
- **`test_execution.log`**: A master aggregated log for the whole suite.

---

## ✅ Verification & Validation

### 💰 Budget & Item Verification
- **Order Summary Integration**: The framework extracts item counts from the **Order Summary** panel for maximum reliability during cart verification.
- **Threshold Validation**: Automatically calculates `items * budget_per_item` to ensure the total subtotal (excluding shipping) meets the required constraints.
- **Variant Persistence**: Retries variant selection if the initial "Add to cart" fails, ensuring complex product selections are registered.

---

## ⚠️ Limitations & Strategic Assumptions

1. **Anti-Bot Interventions**: Certain areas may trigger CAPTCHAs. The framework **pauses for up to 60 seconds** to allow manual human intervention.
2. **Guest Flows**: Default flows operate as a Guest user to minimize account flagging.
3. **Price Extraction**: Logic focuses on the subtotal and item unit price; external costs like shipping or taxes are excluded from the core budget verification logic.

---
*Developed for excellence in eCommerce automation.*
