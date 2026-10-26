"""
conftest.py — Pytest fixtures and hooks for the SkyBook regression suite.

Academic Purpose:
    This module is the backbone of the pytest infrastructure.  It provides:

    1. Cross-browser CLI hooks: --browser and --headless options so the
       suite can be executed against Chrome, Firefox, or Edge without any
       code changes — only a command-line flag changes.

    2. A function-scoped ``driver`` fixture that:
       - Uses ``webdriver-manager`` for zero-configuration driver binary management.
       - Guarantees ``driver.quit()`` is called even if a test fails.

    3. A ``pytest_runtest_makereport`` hook that:
       - On failure, captures a full-viewport screenshot.
       - Attaches the screenshot to BOTH the pytest-html report AND Allure.

    4. Allure integration: failure screenshots and step annotations are
       attached directly to the Allure report for visual debugging.

Design Decision — Function Scope:
    The driver fixture uses ``scope="function"`` so each test receives a
    completely fresh browser session, ensuring test isolation: a failure
    or state change in one test cannot pollute the next.
"""

from __future__ import annotations

import datetime
import re
from pathlib import Path
from typing import Generator

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from config.config import cfg
from utilities.logger import get_logger

logger = get_logger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# CLI option registration
# ──────────────────────────────────────────────────────────────────────────────

def pytest_addoption(parser: pytest.Parser) -> None:
    """
    Register custom command-line options.

    Options:
        --browser   chrome | firefox | edge  (default: chrome)
        --headless  run without a visible browser window (CI-friendly)

    Example:
        pytest --browser=firefox --headless
    """
    parser.addoption(
        "--browser",
        action="store",
        default="chrome",
        choices=["chrome", "firefox", "edge"],
        help="Target browser for test execution (default: chrome).",
    )
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run the browser in headless (no GUI) mode. Recommended for CI.",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Browser driver factory functions
# ──────────────────────────────────────────────────────────────────────────────

def _build_chrome_driver(headless: bool) -> WebDriver:
    """
    Instantiate a Chrome WebDriver via webdriver-manager.

    ``--headless=new`` uses Chrome's modern Blink-based headless mode
    (Chrome 112+) which behaves much more like a real browser than the
    legacy ``--headless`` flag, reducing false-positive test failures.
    """
    options = ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    if headless:
        options.add_argument("--headless=new")

    service = ChromeService(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def _build_firefox_driver(headless: bool) -> WebDriver:
    """Instantiate a Firefox (GeckoDriver) WebDriver via webdriver-manager."""
    options = FirefoxOptions()
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
    if headless:
        options.add_argument("--headless")

    service = FirefoxService(GeckoDriverManager().install())
    return webdriver.Firefox(service=service, options=options)


def _build_edge_driver(headless: bool) -> WebDriver:
    """Instantiate a Microsoft Edge WebDriver via webdriver-manager."""
    options = EdgeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    if headless:
        options.add_argument("--headless=new")

    service = EdgeService(EdgeChromiumDriverManager().install())
    return webdriver.Edge(service=service, options=options)


_DRIVER_BUILDERS = {
    "chrome":  _build_chrome_driver,
    "firefox": _build_firefox_driver,
    "edge":    _build_edge_driver,
}


# ──────────────────────────────────────────────────────────────────────────────
# Driver fixture
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def driver(request: pytest.FixtureRequest) -> Generator[WebDriver, None, None]:
    """
    Function-scoped WebDriver fixture — provides a fresh browser per test.

    Lifecycle:
        SETUP   → reads CLI options, creates the browser driver.
        YIELD   → hands the driver to the test function.
        TEARDOWN → calls driver.quit() regardless of test pass/fail.
    """
    browser: str  = request.config.getoption("--browser",  default="chrome")
    headless: bool = request.config.getoption("--headless", default=False)

    logger.info("Initialising %s WebDriver (headless=%s)", browser, headless)

    builder = _DRIVER_BUILDERS.get(browser)
    if builder is None:
        raise ValueError(
            f"Unsupported browser '{browser}'. Valid options: {list(_DRIVER_BUILDERS.keys())}"
        )

    web_driver = builder(headless)
    web_driver.set_page_load_timeout(cfg.page_load_timeout)
    web_driver.maximize_window()

    # Yield the driver to the test — execution pauses here until the test ends
    yield web_driver

    logger.info("Tearing down %s WebDriver", browser)
    web_driver.quit()


# ──────────────────────────────────────────────────────────────────────────────
# Failure screenshot hook — attaches to both pytest-html AND Allure
# ──────────────────────────────────────────────────────────────────────────────

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """
    Capture a screenshot on test failure and attach to pytest-html and Allure.

    tryfirst=True + hookwrapper=True: ensures this hook runs before other
    hooks and can inspect the completed test outcome.
    """
    outcome = yield
    report  = outcome.get_result()

    # Only capture screenshots for test-body failures (not setup/teardown)
    if report.when == "call" and report.failed:
        web_driver: WebDriver | None = item.funcargs.get("driver")
        if web_driver is None:
            return

        # Build a filesystem-safe filename
        safe_name        = re.sub(r"[^\w\-]", "_", item.name)
        timestamp        = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename         = f"FAIL_{safe_name}_{timestamp}"
        screenshot_path  = cfg.screenshot_dir / f"{filename}.png"

        try:
            web_driver.save_screenshot(str(screenshot_path))
            logger.error("Test FAILED — screenshot: %s", screenshot_path)

            # ── Attach to Allure report (industry standard) ──
            try:
                import allure
                allure.attach(
                    screenshot_path.read_bytes(),
                    name=f"Failure Screenshot — {item.name}",
                    attachment_type=allure.attachment_type.PNG,
                )
                logger.info("Screenshot attached to Allure report")
            except ImportError:
                pass  # allure-pytest is optional

            # ── Attach to pytest-html report (academic fallback) ──
            if not hasattr(report, "extras"):
                report.extras = []
            try:
                from pytest_html import extras as html_extras  # type: ignore
                report.extras.append(html_extras.image(str(screenshot_path)))
                report.extras.append(
                    html_extras.text(
                        f"Screenshot: {screenshot_path}", name="Failure Screenshot Path"
                    )
                )
            except ImportError:
                pass

        except Exception as exc:
            logger.warning("Failed to capture failure screenshot: %s", exc)


# ──────────────────────────────────────────────────────────────────────────────
# HTML report customisation
# ──────────────────────────────────────────────────────────────────────────────

def pytest_html_report_title(report) -> None:
    """Set a professional title for the generated HTML test report."""
    report.title = "SkyBook — Cross-Browser Regression Suite · Test Report"
