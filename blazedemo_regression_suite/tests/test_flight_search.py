"""
test_flight_search.py — Flight search and route selection tests.

Covers:
- Parameterised route matrix: validates that each route returns ≥1 flight
  with a non-empty airline name and a valid numeric price.
"""

from __future__ import annotations

import pytest

from config.config import cfg
from pages.flight_finder_page import FlightFinderPage
from pages.reserve_page import ReservePage
from test_data.booking_payloads import ROUTE_MATRIX
from utilities.logger import get_logger

logger = get_logger(__name__)


class TestFlightSearch:
    """Test class for flight search functionality."""

    @pytest.mark.parametrize(
        "departure, destination",
        ROUTE_MATRIX,
        ids=[f"{dep}->{dst}" for dep, dst in ROUTE_MATRIX],
    )
    @pytest.mark.smoke
    @pytest.mark.regression
    def test_parameterized_route_matrix(
        self,
        driver,
        departure: str,
        destination: str,
    ) -> None:
        """
        Verify that searching for each route in the ROUTE_MATRIX yields at least
        one flight result with a valid airline name and a positive numeric price.

        Steps:
        1. Navigate to BlazeDemo home.
        2. Select the given departure and destination.
        3. Click "Find Flights".
        4. Assert ≥1 flight is listed.
        5. Assert every flight has a non-empty airline and price > 0.

        Args:
            driver:      Injected WebDriver fixture (function-scoped).
            departure:   Departure city string from the parametrize list.
            destination: Destination city string from the parametrize list.
        """
        logger.info("=" * 60)
        logger.info("TEST: route %s → %s", departure, destination)

        # Step 1 — Open home page
        finder = FlightFinderPage(driver)
        finder.open()

        # Step 2–3 — Select route and search
        finder.select_route(departure, destination)
        finder.click_find_flights()

        # Step 4 — Parse results
        reserve = ReservePage(driver)
        flights = reserve.get_available_flights()

        assert len(flights) >= 1, (
            f"Expected at least 1 flight for route {departure}→{destination}, "
            f"got {len(flights)}"
        )
        logger.info("Found %d flight(s) for %s → %s", len(flights), departure, destination)

        # Step 5 — Validate each flight entry
        for flight in flights:
            assert flight["airline"], (
                f"Flight at index {flight['index']} has an empty airline name."
            )
            assert flight["price"] > 0, (
                f"Flight at index {flight['index']} has non-positive price: {flight['price_raw']}"
            )
            logger.info(
                "  ✓ %s | %s | %s → %s",
                flight["airline"],
                flight["price_raw"],
                flight["depart_city"],
                flight["arrive_city"],
            )

        logger.info("PASSED: route %s → %s", departure, destination)

    @pytest.mark.smoke
    def test_home_page_loads(self, driver) -> None:
        """
        Smoke test: verify BlazeDemo home page loads successfully and
        the departure/destination dropdowns are present.
        """
        finder = FlightFinderPage(driver)
        finder.open()

        title = driver.title
        assert "BlazeDemo" in title or title != "", (
            f"Unexpected page title: '{title}'"
        )

        # Verify dropdowns are visible
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        wait = WebDriverWait(driver, cfg.explicit_wait)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "select[name='fromPort']")))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "select[name='toPort']")))

        logger.info("Home page loaded. Title: '%s'", title)
