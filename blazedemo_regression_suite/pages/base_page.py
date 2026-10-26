"""
BasePage — Foundation class for all Page Object Models.

Provides:
- Explicit-wait wrappers (no time.sleep anywhere).
- StaleElementReferenceException retry decorator.
- Scroll-into-view helper.
- Screenshot capture to cfg.screenshot_dir.
"""

from __future__ import annotations

import functools
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, List, Tuple, TypeVar

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait

from config.config import cfg
from utilities.logger import get_logger

F = TypeVar("F", bound=Callable[..., Any])

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Retry decorator for StaleElementReferenceException
# ---------------------------------------------------------------------------

def _retry_on_stale(attempts: int = 3, delay: float = 0.5) -> Callable[[F], F]:
    """
    Decorator that re-invokes a method up to *attempts* times when a
    :class:`StaleElementReferenceException` is raised.
    """
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except StaleElementReferenceException as exc:
                    last_exc = exc
                    logger.warning(
                        "StaleElementReferenceException on '%s' (attempt %d/%d)",
                        fn.__name__,
                        attempt,
                        attempts,
                    )
                    time.sleep(delay)
            raise last_exc  # type: ignore[misc]
        return wrapper  # type: ignore[return-value]
    return decorator


# ---------------------------------------------------------------------------
# BasePage
# ---------------------------------------------------------------------------

class BasePage:
    """
    Base class for all page objects.

    Each page object *must* call ``super().__init__(driver)`` and define
    a ``PAGE_URL`` class attribute if it is a navigable entry point.

    Args:
        driver: Active :class:`WebDriver` instance injected by the fixture.
    """

    PAGE_URL: str = ""

    def __init__(self, driver: WebDriver) -> None:
        self.driver = driver
        self._wait = WebDriverWait(
            driver,
            timeout=cfg.explicit_wait,
            poll_frequency=0.3,
            ignored_exceptions=[StaleElementReferenceException],
        )

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def open(self) -> "BasePage":
        """Navigate to PAGE_URL and return self for method chaining."""
        url = cfg.base_url + self.PAGE_URL if self.PAGE_URL else cfg.base_url
        logger.info("Navigating to: %s", url)
        self.driver.get(url)
        return self

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------

    def _wait_for(
        self,
        condition,
        timeout: int | None = None,
        message: str = "",
    ) -> Any:
        """Generic explicit-wait helper."""
        wait = (
            WebDriverWait(self.driver, timeout, poll_frequency=0.3)
            if timeout
            else self._wait
        )
        return wait.until(condition, message=message)

    def wait_for_visibility(
        self,
        locator: Tuple[str, str],
        timeout: int | None = None,
    ) -> WebElement:
        """Wait until element at *locator* is visible, return it."""
        return self._wait_for(
            EC.visibility_of_element_located(locator),
            timeout=timeout,
            message=f"Element not visible: {locator}",
        )

    def wait_for_clickable(
        self,
        locator: Tuple[str, str],
        timeout: int | None = None,
    ) -> WebElement:
        """Wait until element at *locator* is clickable, return it."""
        return self._wait_for(
            EC.element_to_be_clickable(locator),
            timeout=timeout,
            message=f"Element not clickable: {locator}",
        )

    def wait_for_presence(
        self,
        locator: Tuple[str, str],
        timeout: int | None = None,
    ) -> WebElement:
        """Wait until element at *locator* is present in DOM, return it."""
        return self._wait_for(
            EC.presence_of_element_located(locator),
            timeout=timeout,
            message=f"Element not in DOM: {locator}",
        )

    def wait_for_all_presence(
        self,
        locator: Tuple[str, str],
        timeout: int | None = None,
    ) -> List[WebElement]:
        """Wait until all elements matching *locator* are present, return list."""
        return self._wait_for(
            EC.presence_of_all_elements_located(locator),
            timeout=timeout,
            message=f"Elements not in DOM: {locator}",
        )

    # ------------------------------------------------------------------
    # Action helpers — zero time.sleep
    # ------------------------------------------------------------------

    def _scroll_into_view(self, element: WebElement) -> None:
        """Scroll element into the viewport using JS."""
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});",
            element,
        )

    @_retry_on_stale(attempts=3, delay=0.5)
    def click(self, locator: Tuple[str, str]) -> None:
        """
        Wait for element to be clickable, scroll into view, and click.

        Falls back to JS click if :class:`ElementClickInterceptedException`
        is raised (e.g. element covered by banner/overlay).

        Args:
            locator: A ``(By.*, selector)`` tuple.
        """
        logger.debug("Clicking: %s", locator)
        element = self.wait_for_clickable(locator)
        self._scroll_into_view(element)
        try:
            element.click()
        except ElementClickInterceptedException:
            logger.warning("Regular click intercepted, using JS click for: %s", locator)
            self.driver.execute_script("arguments[0].click();", element)

    @_retry_on_stale(attempts=3, delay=0.5)
    def fill(self, locator: Tuple[str, str], text: str) -> None:
        """
        Wait for visibility, clear the field, and type *text*.

        Args:
            locator: A ``(By.*, selector)`` tuple.
            text:    Text to type into the input field.
        """
        logger.debug("Filling '%s' into: %s", text, locator)
        element = self.wait_for_visibility(locator)
        element.clear()
        element.send_keys(text)

    @_retry_on_stale(attempts=3, delay=0.5)
    def select_by_text(self, locator: Tuple[str, str], text: str) -> None:
        """
        Wait for presence of a ``<select>`` element and select by visible text.

        Args:
            locator: A ``(By.*, selector)`` tuple pointing to the select element.
            text:    The visible option text to select.
        """
        logger.debug("Selecting '%s' in: %s", text, locator)
        element = self.wait_for_presence(locator)
        Select(element).select_by_visible_text(text)

    @_retry_on_stale(attempts=3, delay=0.5)
    def select_by_value(self, locator: Tuple[str, str], value: str) -> None:
        """Select a ``<select>`` option by its value attribute."""
        logger.debug("Selecting value '%s' in: %s", value, locator)
        element = self.wait_for_presence(locator)
        Select(element).select_by_value(value)

    @_retry_on_stale(attempts=3, delay=0.5)
    def get_text(self, locator: Tuple[str, str]) -> str:
        """
        Return the stripped inner text of the located element.

        Args:
            locator: A ``(By.*, selector)`` tuple.

        Returns:
            Stripped text content of the element.
        """
        element = self.wait_for_visibility(locator)
        return element.text.strip()

    @_retry_on_stale(attempts=3, delay=0.5)
    def get_attribute(self, locator: Tuple[str, str], attribute: str) -> str:
        """Return an attribute value from the located element."""
        element = self.wait_for_presence(locator)
        return element.get_attribute(attribute) or ""

    def is_element_present(self, locator: Tuple[str, str], timeout: int = 3) -> bool:
        """Return True if element appears in DOM within *timeout* seconds."""
        try:
            self.wait_for_presence(locator, timeout=timeout)
            return True
        except TimeoutException:
            return False

    # ------------------------------------------------------------------
    # Screenshot
    # ------------------------------------------------------------------

    def take_screenshot(self, filename: str) -> Path:
        """
        Capture the full browser viewport and save to the screenshots directory.

        Args:
            filename: Base filename (without extension) for the PNG file.

        Returns:
            Absolute :class:`Path` of the saved screenshot.
        """
        screenshot_path = cfg.screenshot_dir / f"{filename}.png"
        self.driver.save_screenshot(str(screenshot_path))
        logger.info("Screenshot saved: %s", screenshot_path)
        return screenshot_path

    # ------------------------------------------------------------------
    # Page title / URL helpers
    # ------------------------------------------------------------------

    def get_page_title(self) -> str:
        """Return the current browser page title."""
        return self.driver.title

    def get_current_url(self) -> str:
        """Return the current browser URL."""
        return self.driver.current_url
