"""
FlightFinderPage — BlazeDemo home page.

Handles the departure and destination dropdown selections and
the "Find Flights" form submission.

URL: https://blazedemo.com/
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class FlightFinderPage(BasePage):
    """
    Page Object for the BlazeDemo flight search / home page.

    Locators are defined as class-level tuples following the
    ``(By.*, selector_string)`` convention for clean, maintainable code.
    """

    PAGE_URL: str = "/"

    # ------------------------------------------------------------------
    # Locators
    # ------------------------------------------------------------------

    _FROM_PORT_SELECT = (By.CSS_SELECTOR, "select[name='fromPort']")
    _TO_PORT_SELECT   = (By.CSS_SELECTOR, "select[name='toPort']")
    _FIND_FLIGHTS_BTN = (By.CSS_SELECTOR, "input[type='submit']")

    # Heading to confirm correct page is loaded
    _PAGE_HEADING     = (By.CSS_SELECTOR, "h3")

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------

    def __init__(self, driver: WebDriver) -> None:
        super().__init__(driver)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def select_route(self, departure: str, destination: str) -> "FlightFinderPage":
        """
        Select the departure and destination airports from the dropdowns.

        Args:
            departure:   Visible text of the departure city (e.g. "Paris").
            destination: Visible text of the destination city (e.g. "Buenos Aires").

        Returns:
            Self for fluent/method-chaining usage.
        """
        logger.info("Selecting route: %s → %s", departure, destination)
        self.select_by_text(self._FROM_PORT_SELECT, departure)
        self.select_by_text(self._TO_PORT_SELECT, destination)
        return self

    def click_find_flights(self) -> None:
        """
        Click the "Find Flights" submit button.

        After clicking, the browser navigates to the Reserve page; callers
        should instantiate :class:`~pages.reserve_page.ReservePage` next.
        """
        logger.info("Clicking 'Find Flights'")
        self.click(self._FIND_FLIGHTS_BTN)

    def get_heading(self) -> str:
        """Return the page heading text (e.g. 'Welcome to the Simple Travel Agency!')."""
        return self.get_text(self._PAGE_HEADING)
