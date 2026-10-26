"""
ReservePage — BlazeDemo flight results listing page.

Parses the available flights table, exposes structured flight data,
and allows selection of a specific flight or the cheapest option.

URL: https://blazedemo.com/reserve.php
"""

from __future__ import annotations

import re
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class ReservePage(BasePage):
    """
    Page Object for the flight results (reserve) page.

    Key responsibilities:
    - Parse all available flight rows from the HTML table.
    - Return structured dictionaries with airline, price, departure/arrival airports.
    - Select a flight by index or select the cheapest available flight.
    """

    PAGE_URL: str = "/reserve.php"

    # ------------------------------------------------------------------
    # Locators
    # ------------------------------------------------------------------

    _PAGE_HEADING    = (By.CSS_SELECTOR, "h3")
    _FLIGHT_ROWS     = (By.XPATH, "//table/tbody/tr")
    _CHOOSE_BTNS     = (By.CSS_SELECTOR, "table tbody tr input[type='submit']")

    # Column indices within each row (0-based)
    _COL_DEPART_CITY  = 1
    _COL_ARRIVE_CITY  = 2
    _COL_DEPART_TIME  = 3
    _COL_ARRIVE_TIME  = 4
    _COL_AIRLINE      = 5
    _COL_PRICE        = 6

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------

    def __init__(self, driver: WebDriver) -> None:
        super().__init__(driver)

    # ------------------------------------------------------------------
    # Data extraction helpers
    # ------------------------------------------------------------------

    def get_available_flights(self) -> List[dict]:
        """
        Parse all flight rows from the results table.

        Returns:
            List of dicts, each containing:
            ``index``, ``airline``, ``price`` (float),
            ``depart_city``, ``arrive_city``,
            ``depart_time``, ``arrive_time``.

        Raises:
            AssertionError: If no flight rows are found.
        """
        logger.info("Parsing available flights from results table")
        rows = self.wait_for_all_presence(self._FLIGHT_ROWS)
        flights: List[dict] = []

        for idx, row in enumerate(rows):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) < 7:
                    continue  # skip malformed rows

                price_raw = cells[self._COL_PRICE].text.strip()
                # Extract numeric value: "$472.56" → 472.56
                price_match = re.search(r"[\d,]+\.?\d*", price_raw.replace(",", ""))
                price_float = float(price_match.group()) if price_match else 0.0

                flights.append(
                    {
                        "index": idx,
                        "airline":      cells[self._COL_AIRLINE].text.strip(),
                        "price":        price_float,
                        "price_raw":    price_raw,
                        "depart_city":  cells[self._COL_DEPART_CITY].text.strip(),
                        "arrive_city":  cells[self._COL_ARRIVE_CITY].text.strip(),
                        "depart_time":  cells[self._COL_DEPART_TIME].text.strip(),
                        "arrive_time":  cells[self._COL_ARRIVE_TIME].text.strip(),
                    }
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not parse row %d: %s", idx, exc)

        logger.info("Found %d available flight(s)", len(flights))
        return flights

    # ------------------------------------------------------------------
    # Selection actions
    # ------------------------------------------------------------------

    def choose_flight_by_index(self, index: int = 0) -> dict:
        """
        Click the "Choose This Flight" button for the flight at *index*.

        Args:
            index: Zero-based index of the flight row to choose.

        Returns:
            The flight dict for the chosen flight (captured before click).
        """
        flights = self.get_available_flights()
        if not flights:
            raise AssertionError("No flights available to choose from.")
        if index >= len(flights):
            raise IndexError(
                f"Flight index {index} out of range (found {len(flights)} flights)."
            )

        chosen = flights[index]
        logger.info(
            "Choosing flight index %d: %s @ %s",
            index,
            chosen["airline"],
            chosen["price_raw"],
        )

        # Click the corresponding button — use nth-of-type to target specific row
        buttons = self.wait_for_all_presence(self._CHOOSE_BTNS)
        self._scroll_into_view(buttons[index])
        buttons[index].click()

        return chosen

    def choose_cheapest_flight(self) -> dict:
        """
        Identify and select the lowest-priced flight from the results table.

        Returns:
            The flight dict for the cheapest option (captured before click).
        """
        flights = self.get_available_flights()
        if not flights:
            raise AssertionError("No flights available to compare.")

        cheapest = min(flights, key=lambda f: f["price"])
        logger.info(
            "Cheapest flight: %s @ %s (index %d)",
            cheapest["airline"],
            cheapest["price_raw"],
            cheapest["index"],
        )
        return self.choose_flight_by_index(cheapest["index"])

    # ------------------------------------------------------------------
    # Assertions helpers
    # ------------------------------------------------------------------

    def get_heading(self) -> str:
        """Return the results page heading text."""
        return self.get_text(self._PAGE_HEADING)

    def flight_count(self) -> int:
        """Return the number of available flights in the results table."""
        return len(self.get_available_flights())
