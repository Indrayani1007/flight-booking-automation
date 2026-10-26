"""
flight_finder_page.py — SkyBook Home / Search Page Object.

Maps to: http://localhost:8000/index.html

Responsibilities:
    - Select departure and destination cities from the dynamic <select> dropdowns.
    - Set the travel date.
    - Set the passenger count.
    - Submit the search form.

Locator Strategy:
    All locators use ``data-testid`` attributes added specifically for automation.
    This decouples the test suite from volatile CSS class names and fragile XPaths,
    which is an industry best practice for maintainable Selenium tests.
"""

from __future__ import annotations

import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class FlightFinderPage(BasePage):
    """
    Page Object representing the SkyBook flight search (home) page.

    Encapsulates all locators and interactions with the search widget,
    exposing a clean, business-readable API to the test layer.
    """

    # ── Locators ──────────────────────────────────────────────────────────────
    # Using data-testid attributes for stability — these attributes are explicitly
    # added to the HTML for automation and do not change with visual redesigns.

    _DEPARTURE_SELECT   = (By.CSS_SELECTOR, "[data-testid='departure-select']")
    _DESTINATION_SELECT = (By.CSS_SELECTOR, "[data-testid='destination-select']")
    _DATE_INPUT         = (By.CSS_SELECTOR, "[data-testid='travel-date']")
    _PASSENGERS_SELECT  = (By.CSS_SELECTOR, "[data-testid='passengers-select']")
    _SEARCH_BUTTON      = (By.CSS_SELECTOR, "[data-testid='search-button']")
    _ERROR_BANNER       = (By.ID, "form-error")

    # ── Public API ────────────────────────────────────────────────────────────

    def open(self) -> "FlightFinderPage":
        """Navigate to the home page and wait for the search form to render."""
        super().open("")  # Opens index.html
        # Wait for the search form to be present before returning
        self.wait_for_visible(self._SEARCH_BUTTON)
        logger.info("FlightFinderPage loaded")
        return self

    def select_departure(self, city: str) -> "FlightFinderPage":
        """
        Select a departure city from the dropdown.

        Uses select_by_value which is more reliable than select_by_text because
        the value attribute is the canonical city name in this application.

        Args:
            city: Exact city name matching a dropdown option value.
        """
        self.select_by_value(self._DEPARTURE_SELECT, city)
        logger.info("Selected departure: %s", city)
        return self  # Fluent interface — allows method chaining

    def select_destination(self, city: str) -> "FlightFinderPage":
        """
        Select a destination city from the dropdown.

        Args:
            city: Exact city name matching a dropdown option value.
        """
        self.select_by_value(self._DESTINATION_SELECT, city)
        logger.info("Selected destination: %s", city)
        return self

    def set_travel_date(self, date_str: str) -> "FlightFinderPage":
        """
        Set the travel date input field.

        Args:
            date_str: Date string in YYYY-MM-DD format (HTML date input standard).
        """
        # JavaScript date input requires direct value injection for reliability
        # across Chrome/Firefox/Edge because send_keys behaves differently per browser
        el = self.wait_for_visible(self._DATE_INPUT)
        self.driver.execute_script(
            "arguments[0].value = arguments[1];", el, date_str
        )
        logger.info("Set travel date: %s", date_str)
        return self

    def set_passengers(self, count: int) -> "FlightFinderPage":
        """
        Select the number of passengers.

        Args:
            count: Integer between 1 and 9 matching a dropdown option.
        """
        self.select_by_value(self._PASSENGERS_SELECT, str(count))
        logger.info("Set passengers: %d", count)
        return self

    def select_route(self, departure: str, destination: str) -> "FlightFinderPage":
        """Convenience method: select both departure and destination in one call."""
        return self.select_departure(departure).select_destination(destination)

    def click_search(self) -> None:
        """
        Click the 'Search Available Flights' submit button.

        After clicking, the browser navigates to results.html, so the caller
        should switch to a ResultsPage object.
        """
        self.click(self._SEARCH_BUTTON)
        logger.info("Search form submitted")

    # Alias kept for backward compatibility with existing test files
    def click_find_flights(self) -> None:
        """Alias for click_search() — backward-compatible method name."""
        self.click_search()

    def get_error_message(self) -> str:
        """
        Return the text of the validation error banner (if visible).

        Used in negative tests to assert that the application correctly
        displays validation errors for invalid form input.
        """
        return self.get_text(self._ERROR_BANNER)

    def is_error_visible(self) -> bool:
        """Return True if the validation error banner is currently displayed."""
        try:
            el = self.wait_for_visible(self._ERROR_BANNER, timeout=3)
            return el.is_displayed()
        except Exception:
            return False
