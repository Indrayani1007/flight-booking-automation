"""
conftest.py — Pytest fixtures and hooks for BlazeDemo regression suite.

Provides:
- CLI option hooks: --browser (chrome/firefox/edge) and --headless.
- ``driver`` fixture (function-scoped): creates and tears down WebDriver.
- ``pytest_runtest_makereport``: captures screenshots on test failure and
  attaches them to the pytest-html report.
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


# ---------------------------------------------------------------------------
# CLI option registration
# ---------------------------------------------------------------------------

def pytest_addoption(parser: pytest.Parser) -> None:
    """Register custom CLI arguments for the test suite."""
    parser.addoption(
        "--browser",
        action="store",
        default="chrome",
        choices=["chrome", "firefox", "edge"],
        help="Browser to run tests against (default: chrome).",
    )
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode (recommended for CI).",
    )


# ---------------------------------------------------------------------------
# Driver factory helpers
# ---------------------------------------------------------------------------

def _build_chrome_driver(headless: bool) -> WebDriver:
    """Instantiate a Chrome WebDriver with optional headless mode."""
    options = ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    if headless:
        options.add_argument("--headless=new")
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def _build_firefox_driver(headless: bool) -> WebDriver:
    """Instantiate a Firefox (Gecko) WebDriver with optional headless mode."""
    options = FirefoxOptions()
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")
    if headless:
        options.add_argument("--headless")
    service = FirefoxService(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    return driver


def _build_edge_driver(headless: bool) -> WebDriver:
    """Instantiate an Edge (Chromium) WebDriver with optional headless mode."""
    options = EdgeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    if headless:
        options.add_argument("--headless=new")
    service = EdgeService(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=options)
    return driver


_DRIVER_BUILDERS = {
    "chrome":  _build_chrome_driver,
    "firefox": _build_firefox_driver,
    "edge":    _build_edge_driver,
}


# ---------------------------------------------------------------------------
# Driver fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def driver(request: pytest.FixtureRequest) -> Generator[WebDriver, None, None]:
    """
    Function-scoped WebDriver fixture.

    Reads ``--browser`` and ``--headless`` from CLI options, creates the
    appropriate driver, sets page-load timeout, and ensures ``driver.quit()``
    is called in teardown regardless of test outcome.

    Yields:
        Active :class:`WebDriver` instance.
    """
    browser: str = request.config.getoption("--browser", default="chrome")
    headless: bool = request.config.getoption("--headless", default=False)

    logger.info("Starting %s driver (headless=%s)", browser, headless)

    builder = _DRIVER_BUILDERS.get(browser)
    if builder is None:
        raise ValueError(
            f"Unsupported browser '{browser}'. Choose from: {list(_DRIVER_BUILDERS)}"
        )

    web_driver = builder(headless)
    web_driver.set_page_load_timeout(cfg.page_load_timeout)
    web_driver.maximize_window()

    yield web_driver

    logger.info("Quitting %s driver", browser)
    web_driver.quit()


# ---------------------------------------------------------------------------
# Screenshot on failure hook
# ---------------------------------------------------------------------------

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    """
    pytest hook that fires after each test phase (setup / call / teardown).

    When the *call* phase fails, a timestamped screenshot is saved to
    ``reports/screenshots/`` and attached to the pytest-html report.
    """
    outcome = yield  # let the test run
    report = outcome.get_result()

    # Only act on failures during the actual test call (not setup/teardown)
    if report.when == "call" and report.failed:
        web_driver: WebDriver | None = item.funcargs.get("driver")
        if web_driver is None:
            return

        # Sanitise the test name to create a valid filename
        safe_name = re.sub(r"[^\w\-]", "_", item.name)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"FAIL_{safe_name}_{timestamp}"

        screenshot_path: Path = cfg.screenshot_dir / f"{filename}.png"
        try:
            web_driver.save_screenshot(str(screenshot_path))
            logger.error("Failure screenshot saved: %s", screenshot_path)

            # Attach to pytest-html report if the plugin is available
            extras_attr = getattr(report, "extras", None)
            if extras_attr is None:
                report.extras = []
            try:
                from pytest_html import extras as html_extras  # type: ignore

                report.extras.append(
                    html_extras.image(str(screenshot_path))
                )
                report.extras.append(
                    html_extras.text(f"Screenshot: {screenshot_path}", name="Screenshot Path")
                )
            except ImportError:
                pass  # pytest-html not installed; skip attachment
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not capture failure screenshot: %s", exc)


# ---------------------------------------------------------------------------
# HTML report title customisation
# ---------------------------------------------------------------------------

def pytest_html_report_title(report) -> None:
    """Set a custom title for the HTML report."""
    report.title = "BlazeDemo Regression Suite — Test Report"
