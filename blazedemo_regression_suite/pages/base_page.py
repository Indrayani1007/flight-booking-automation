"""
base_page.py — Foundation Page Object for the SkyBook Regression Suite.

Academic Purpose:
    The BasePage class implements the Page Object Model (POM) foundation layer.
    Every concrete page class (FlightFinderPage, ResultsPage, etc.) inherits
    from BasePage, which centralises all low-level Selenium interactions.

    Why this pattern?
    ─────────────────
    Without a base class, every page object would repeat the same WebDriverWait
    boilerplate.  A bug in the wait strategy would need fixing in N places.
    With BasePage, fixing the wait strategy here propagates to all pages — this
    is the Open/Closed Principle applied to test automation.

Key Design Decisions:
    1. ALL interactions go through explicit waits — time.sleep() is never used.
    2. Stale element retries prevent flaky failures on dynamic pages.
    3. screenshot() is available to any page for on-demand debugging.
"""

from __future__ import annotations

import datetime
import functools
import logging
import time
from pathlib import Path
from typing import Callable, List

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

logger = logging.getLogger(__name__)


def _retry_on_stale(max_attempts: int = 3, delay: float = 0.5):
    """
    Decorator factory: retry the wrapped method when a StaleElementReferenceException
    is raised.

    Why stale element exceptions occur:
        Modern single-page applications re-render parts of the DOM after a user
        action (e.g., search results replacing a spinner).  A WebElement reference
        obtained before the re-render becomes "stale" and raises this exception.

    Strategy:
        Wait `delay` seconds and retry up to `max_attempts` times before giving up.
        This mirrors how a real user would naturally wait and retry.
    """
    def decorator(fn: Callable):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except StaleElementReferenceException as exc:
                    last_exc = exc
                    logger.warning(
                        "StaleElementReferenceException on attempt %d/%d for '%s'",
                        attempt, max_attempts, fn.__name__,
                    )
                    time.sleep(delay)
            raise last_exc
        return wrapper
    return decorator


class BasePage:
    """
    Abstract foundation for all SkyBook page objects.

    Constructor Args:
        driver: Active WebDriver session managed by the pytest fixture.
    """

    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver
        from config.config import cfg  # Lazy import avoids circular dependency
        self._wait = WebDriverWait(driver, cfg.explicit_wait)
        self._cfg  = cfg

    # ──────────────────────────────────────────────────────────────────────────
    # Navigation
    # ──────────────────────────────────────────────────────────────────────────

    def open(self, path: str = "") -> None:
        """
        Navigate to a URL path relative to the configured base URL.

        Args:
            path: Relative path (e.g., "results.html"). Empty string → home page.
        """
        url = f"{self._cfg.base_url}/{path}".rstrip("/")
        # Ensure we always open from root when path is empty
        if not path:
            url = self._cfg.base_url + "/index.html"
        logger.info("Navigating to: %s", url)
        self.driver.get(url)

    # ──────────────────────────────────────────────────────────────────────────
    # Core wait wrappers — every interaction uses one of these
    # ──────────────────────────────────────────────────────────────────────────

    def wait_for_visible(self, locator: tuple, timeout: int | None = None) -> WebElement:
        """
        Wait until the element identified by ``locator`` is visible in the DOM.

        Visibility means the element exists AND occupies space on the page
        (i.e., it is not hidden with ``display:none`` or ``visibility:hidden``).

        Args:
            locator: A (By.X, value) tuple — e.g., (By.ID, "departure").
            timeout: Optional override in seconds; defaults to config value.

        Returns:
            The visible WebElement ready for interaction.

        Raises:
            TimeoutException: If the element does not become visible within timeout.
        """
        wait = WebDriverWait(self.driver, timeout) if timeout else self._wait
        try:
            return wait.until(EC.visibility_of_element_located(locator))
        except TimeoutException:
            logger.error("Timeout waiting for visible: %s", locator)
            raise

    def wait_for_clickable(self, locator: tuple, timeout: int | None = None) -> WebElement:
        """
        Wait until the element is visible AND enabled (i.e., safe to click).

        'Clickable' is a stricter condition than 'visible' — it ensures the element
        is not disabled and is interactable, preventing ElementNotInteractableError.
        """
        wait = WebDriverWait(self.driver, timeout) if timeout else self._wait
        try:
            return wait.until(EC.element_to_be_clickable(locator))
        except TimeoutException:
            logger.error("Timeout waiting for clickable: %s", locator)
            raise

    def wait_for_presence(self, locator: tuple, timeout: int | None = None) -> WebElement:
        """
        Wait until the element is present in the DOM (not necessarily visible).

        Used for hidden elements whose text/attributes we need to read before
        they become visible.
        """
        wait = WebDriverWait(self.driver, timeout) if timeout else self._wait
        return wait.until(EC.presence_of_element_located(locator))

    def wait_for_all_visible(self, locator: tuple, timeout: int | None = None) -> List[WebElement]:
        """
        Wait until ALL elements matching ``locator`` are visible.
        Used to wait for dynamically generated lists (e.g., flight cards).
        """
        wait = WebDriverWait(self.driver, timeout) if timeout else self._wait
        return wait.until(EC.visibility_of_all_elements_located(locator))

    def wait_for_invisible(self, locator: tuple, timeout: int | None = None) -> bool:
        """
        Wait until the element matching ``locator`` is no longer visible.

        Critical for spinner-based loading patterns: we must wait for the
        spinner to disappear before the results are ready to interact with.
        Returns True once the element is invisible/gone.
        """
        wait = WebDriverWait(self.driver, timeout) if timeout else self._wait
        try:
            return wait.until(EC.invisibility_of_element_located(locator))
        except TimeoutException:
            logger.error("Spinner/element did not disappear: %s", locator)
            raise

    def wait_for_url_contains(self, fragment: str, timeout: int | None = None) -> bool:
        """Wait until the current URL contains ``fragment``."""
        wait = WebDriverWait(self.driver, timeout) if timeout else self._wait
        return wait.until(EC.url_contains(fragment))

    # ──────────────────────────────────────────────────────────────────────────
    # Interaction helpers
    # ──────────────────────────────────────────────────────────────────────────

    @_retry_on_stale()
    def click(self, locator: tuple) -> None:
        """Wait for element to be clickable, then click it."""
        self.wait_for_clickable(locator).click()

    @_retry_on_stale()
    def type_text(self, locator: tuple, text: str, clear_first: bool = True) -> None:
        """
        Wait for an input field, optionally clear it, then type the given text.

        Clearing before typing prevents text accumulation when a test re-uses
        an already-filled field, which is a common source of flaky tests.
        """
        el = self.wait_for_visible(locator)
        if clear_first:
            el.clear()
        el.send_keys(text)

    @_retry_on_stale()
    def select_by_value(self, locator: tuple, value: str) -> None:
        """Select a <select> dropdown option by its ``value`` attribute."""
        el = self.wait_for_visible(locator)
        Select(el).select_by_value(value)

    @_retry_on_stale()
    def select_by_text(self, locator: tuple, text: str) -> None:
        """Select a <select> dropdown option by its visible text."""
        el = self.wait_for_visible(locator)
        Select(el).select_by_visible_text(text)

    def clear_field(self, locator: tuple) -> None:
        """Clear the content of a form input identified by ``locator``."""
        el = self.wait_for_visible(locator)
        el.clear()

    @_retry_on_stale()
    def get_text(self, locator: tuple) -> str:
        """Return the visible text of an element (stripped of whitespace)."""
        return self.wait_for_visible(locator).text.strip()

    @_retry_on_stale()
    def get_attribute(self, locator: tuple, attr: str) -> str:
        """Return the value of an HTML attribute on the located element."""
        return self.wait_for_presence(locator).get_attribute(attr) or ""

    # ──────────────────────────────────────────────────────────────────────────
    # Debugging helpers
    # ──────────────────────────────────────────────────────────────────────────

    def screenshot(self, name: str = "screenshot") -> Path:
        """
        Save a full-viewport screenshot to the configured screenshot directory.

        Args:
            name: Base filename (without extension). A timestamp is appended.

        Returns:
            Path to the saved PNG file.
        """
        ts   = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self._cfg.screenshot_dir / f"{name}_{ts}.png"
        self.driver.save_screenshot(str(path))
        logger.info("Screenshot saved: %s", path)
        return path

    @property
    def current_url(self) -> str:
        """Return the browser's current URL."""
        return self.driver.current_url

    @property
    def title(self) -> str:
        """Return the browser page title."""
        return self.driver.title
