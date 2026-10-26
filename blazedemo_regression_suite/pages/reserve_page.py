"""
reserve_page.py — SkyBook Flight Results Page Object.

Maps to: http://localhost:8000/results.html

Key Challenge — Async Loading Spinner:
    After the search form is submitted, the results page shows a 2-second
    animated spinner while "fetching" data.  Selenium must NOT interact with
    the flight cards until the spinner has completely disappeared and the
    results grid is visible.

    Incorrect approach:  time.sleep(3)     — brittle, slow, never times correctly
    Correct approach:    WebDriverWait(...).until(EC.invisibility_of_element_located(...))

    This page object correctly handles the async pattern using explicit waits,
    demonstrating a real-world synchronization challenge and its professional solution.
"""

from __future__ import annotations

import logging
import re
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class ReservePage(BasePage):
    """
    Page Object representing the SkyBook flight results page.

    Waits for the async loading spinner, then provides access to the
    dynamically generated flight card list.
    """

    # ── Locators ──────────────────────────────────────────────────────────────

    # Spinner: visible during the 2-second async loading phase
    _SPINNER          = (By.CSS_SELECTOR, "[data-testid='loading-spinner']")
    # Results container: hidden while spinner is active, then shown
    _RESULTS_CONTAINER = (By.CSS_SELECTOR, "[data-testid='results-container']")
    # Individual flight cards — all cards share this data-testid
    _FLIGHT_CARDS     = (By.CSS_SELECTOR, "[data-testid='flight-card']")
    # Price labels within each card
    _FLIGHT_PRICES    = (By.CSS_SELECTOR, "[data-testid='flight-price']")
    # The "Select Flight" buttons (one per card)
    _SELECT_BUTTONS   = (By.CSS_SELECTOR, ".select-flight-btn")
    # Search summary text at the top of the results page
    _SEARCH_SUMMARY   = (By.CSS_SELECTOR, "[data-testid='search-summary']")
    # Count label: "N flights found"
    _RESULTS_COUNT    = (By.CSS_SELECTOR, "[data-testid='results-count']")

    # ── Spinner wait ──────────────────────────────────────────────────────────

    def wait_for_results(self, timeout: int = 10) -> "ReservePage":
        """
        Wait for the 2-second async spinner to disappear and results to load.

        This is the critical synchronization point for this page.  We use TWO
        sequential waits:
          1. wait_for_invisible(spinner): confirms the data-fetch phase ended.
          2. wait_for_visible(results_container): confirms the DOM is populated.

        Using both waits makes the suite robust against slow/variable JavaScript
        execution — a common real-world scenario.

        Args:
            timeout: Maximum seconds to wait (default: 10, well above the 2s spinner).
        """
        logger.info("Waiting for search spinner to disappear…")
        self.wait_for_invisible(self._SPINNER, timeout=timeout)
        logger.info("Spinner gone — waiting for results to render…")
        self.wait_for_visible(self._RESULTS_CONTAINER, timeout=timeout)
        logger.info("Flight results are now visible")
        return self

    # ── Flight card interactions ───────────────────────────────────────────────

    def flight_count(self) -> int:
        """
        Return the number of flight cards currently displayed.

        Calls wait_for_results() internally so it is always safe to call
        this method without a preceding wait.
        """
        self.wait_for_results()
        cards = self.driver.find_elements(*self._FLIGHT_CARDS)
        count = len(cards)
        logger.info("Found %d flight card(s)", count)
        return count

    def get_all_prices(self) -> List[float]:
        """
        Extract and return all displayed flight prices as floats.

        Prices are rendered as "$NNN.NN" — we strip the '$' and parse the
        numeric value for assertion comparisons.

        Returns:
            List of float prices (e.g., [612.35, 503.20]).
        """
        self.wait_for_results()
        price_els = self.driver.find_elements(*self._FLIGHT_PRICES)
        prices = []
        for el in price_els:
            raw = el.text.strip()
            # Extract numeric value; regex handles format like "$1,234.56"
            match = re.search(r"[\d,]+\.?\d*", raw)
            if match:
                prices.append(float(match.group().replace(",", "")))
        logger.info("Extracted prices: %s", prices)
        return prices

    def choose_flight_by_index(self, index: int = 0) -> None:
        """
        Click the 'Select Flight' button for the flight at the given index.

        Args:
            index: Zero-based index (0 = first result, 1 = second, etc.).

        Raises:
            IndexError: If index exceeds the number of available flights.
        """
        self.wait_for_results()
        buttons = self.driver.find_elements(*self._SELECT_BUTTONS)
        if index >= len(buttons):
            raise IndexError(
                f"Requested index {index} but only {len(buttons)} flights available."
            )
        button = buttons[index]
        # Scroll the button into view before clicking — prevents ElementClickInterceptedException
        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", button)
        button.click()
        logger.info("Selected flight at index %d", index)

    def get_search_summary(self) -> str:
        """Return the search summary text displayed above the results."""
        return self.get_text(self._SEARCH_SUMMARY)

    def get_results_count_text(self) -> str:
        """Return the results count label text (e.g., '2 flights found')."""
        self.wait_for_results()
        return self.get_text(self._RESULTS_COUNT)

    # Backward-compatible alias
    def get_flight_count(self) -> int:
        """Alias for flight_count() — retained for backward compatibility."""
        return self.flight_count()
