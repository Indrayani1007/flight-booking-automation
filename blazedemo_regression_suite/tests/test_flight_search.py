"""
test_flight_search.py — Search Functionality & Route Validation Tests.

Test Coverage:
    1. Smoke test: page loads with correct title.
    2. UI validation: dropdown population check.
    3. Default search: clicking search with pre-selected defaults returns results.
    4. Parameterized route matrix: multiple city pairs all return ≥1 results.
    5. Same-city validation: selecting identical dep/dest shows error.

These tests validate the top of the booking funnel (search → results).
"""

from __future__ import annotations

import pytest
import allure

from pages.flight_finder_page import FlightFinderPage
from pages.reserve_page import ReservePage
from test_data.booking_payloads import ROUTE_MATRIX, TOMORROW


@allure.feature("Flight Search")
class TestFlightSearch:
    """Tests for the SkyBook flight search and results pages."""

    @allure.story("Page Load")
    @allure.title("Home page loads with correct title")
    @pytest.mark.smoke
    def test_home_page_title(self, driver) -> None:
        """
        Smoke test: navigate to the home page and verify the page title.

        This is the simplest possible test — it verifies the application
        is running and reachable before executing more complex scenarios.
        """
        with allure.step("Open SkyBook home page"):
            page = FlightFinderPage(driver)
            page.open()

        with allure.step("Verify page title contains 'SkyBook'"):
            title = driver.title
            assert "SkyBook" in title, (
                f"Expected 'SkyBook' in page title, but got: '{title}'. "
                "The web server may not be running or base_url is misconfigured."
            )

    @allure.story("Search Form")
    @allure.title("Search dropdowns are populated with city options")
    @pytest.mark.smoke
    def test_search_dropdowns_populated(self, driver) -> None:
        """
        UI validation: verify the departure and destination dropdowns contain options.

        JavaScript populates the dropdowns dynamically from the FLIGHTS dataset.
        This test confirms the JS has run correctly and the DOM has options.
        """
        with allure.step("Open home page"):
            page = FlightFinderPage(driver)
            page.open()

        with allure.step("Count departure dropdown options"):
            from selenium.webdriver.common.by import By
            dep_options = driver.find_elements(By.CSS_SELECTOR, "#departure option")
            assert len(dep_options) > 1, (
                "Departure dropdown has only 1 option (the placeholder). "
                "JavaScript may have failed to populate it."
            )

        with allure.step("Count destination dropdown options"):
            dest_options = driver.find_elements(By.CSS_SELECTOR, "#destination option")
            assert len(dest_options) > 1, (
                "Destination dropdown has only 1 option (the placeholder). "
                "JavaScript may have failed to populate it."
            )

    @allure.story("Default Search")
    @allure.title("Search with default selections returns flight results")
    @pytest.mark.regression
    def test_default_search_returns_results(self, driver) -> None:
        """
        Default-state test: search with the pre-selected defaults (Philadelphia → Buenos Aires).

        The dropdowns auto-select these defaults on page load. This verifies
        the application works correctly without any user interaction on the form.
        """
        with allure.step("Open home page with default city selections"):
            page = FlightFinderPage(driver)
            page.open()

        with allure.step("Submit search with default values"):
            page.click_search()

        with allure.step("Wait for results to load after spinner"):
            reserve = ReservePage(driver)
            count = reserve.flight_count()

        with allure.step("Assert at least 1 result is displayed"):
            assert count >= 1, (
                f"Expected ≥1 flights with default route (Philadelphia → Buenos Aires), "
                f"but found {count}. Check the flight dataset in app.js."
            )

    @allure.story("Same-City Validation")
    @allure.title("Same city for departure and destination shows validation error")
    @pytest.mark.negative
    def test_same_city_shows_error(self, driver) -> None:
        """
        Negative test: selecting the same city for departure and destination
        should trigger the application's client-side validation error.
        """
        with allure.step("Open home page"):
            page = FlightFinderPage(driver)
            page.open()

        with allure.step("Select same city for departure and destination"):
            page.select_departure("New York")
            page.select_destination("New York")

        with allure.step("Submit search"):
            page.click_search()

        with allure.step("Assert validation error is displayed"):
            assert page.is_error_visible(), (
                "Expected a validation error when selecting the same city for "
                "departure and destination, but no error was shown."
            )
            error_text = page.get_error_message()
            assert len(error_text) > 0, "Validation error banner is empty."

    @allure.story("Route Matrix")
    @pytest.mark.parametrize("departure,destination,min_flights", ROUTE_MATRIX)
    @pytest.mark.regression
    def test_parameterized_route_matrix(
        self, driver, departure: str, destination: str, min_flights: int
    ) -> None:
        """
        Parameterized test: verify that multiple city-pair routes all return results.

        pytest.mark.parametrize runs this test once for each row in ROUTE_MATRIX,
        generating individual pass/fail entries per route in the report.
        This is an efficient way to achieve broad route coverage.

        Args:
            departure:   Departure city name.
            destination: Destination city name.
            min_flights: Minimum expected flight count for this route.
        """
        allure.dynamic.title(f"Route: {departure} → {destination}")

        with allure.step(f"Open home page and select route {departure} → {destination}"):
            page = FlightFinderPage(driver)
            page.open()
            page.select_route(departure, destination)
            page.set_travel_date(TOMORROW)

        with allure.step("Submit search"):
            page.click_search()

        with allure.step(f"Verify ≥{min_flights} result(s) returned"):
            reserve = ReservePage(driver)
            count   = reserve.flight_count()
            assert count >= min_flights, (
                f"Route {departure} → {destination}: expected ≥{min_flights} flight(s), "
                f"but got {count}. Verify the FLIGHTS dataset in app.js includes this route."
            )
