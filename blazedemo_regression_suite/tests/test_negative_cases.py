"""
test_negative_cases.py — Boundary and Negative Test Cases for SkyBook.

Academic Purpose:
    Negative testing verifies graceful handling of invalid, missing, or
    unexpected input. A test suite covering only happy paths provides a
    false sense of security.

    Categories tested:
    1. Same-city validation error on search form.
    2. Checkout form validation: missing name triggers error.
    3. Checkout form validation: invalid email triggers error.
    4. Checkout form validation: short card number triggers error.
    5. Direct URL access to checkout.html without a prior selection.
"""

from __future__ import annotations

import allure
import pytest

from pages.confirmation_page import ConfirmationPage
from pages.flight_finder_page import FlightFinderPage
from pages.purchase_page import PurchasePage
from pages.reserve_page import ReservePage
from test_data.booking_payloads import (
    E2E_ROUTE,
    INVALID_PASSENGER_DATA_BAD_EMAIL,
    INVALID_PASSENGER_DATA_MISSING_NAME,
    INVALID_PASSENGER_DATA_SHORT_CARD,
    TOMORROW,
    VALID_PASSENGER_DATA,
)
from utilities.logger import get_logger

logger = get_logger(__name__)


def _navigate_to_checkout(driver) -> PurchasePage:
    """Helper: navigate through search → results → checkout and return PurchasePage."""
    dep, dest = E2E_ROUTE
    finder = FlightFinderPage(driver)
    finder.open()
    finder.select_route(dep, dest)
    finder.set_travel_date(TOMORROW)
    finder.click_search()

    reserve = ReservePage(driver)
    reserve.choose_flight_by_index(0)

    purchase = PurchasePage(driver)
    purchase.wait_for_page_load()
    return purchase


@allure.feature("Form Validation")
class TestNegativeCases:
    """Negative and boundary test cases."""

    @allure.story("Search Validation")
    @allure.title("Same city for departure and destination shows error")
    @pytest.mark.negative
    def test_same_city_validation_error(self, driver) -> None:
        """Selecting identical departure and destination should show a validation error."""
        with allure.step("Open home page"):
            page = FlightFinderPage(driver)
            page.open()

        with allure.step("Select same city for both departure and destination"):
            page.select_departure("Chicago")
            page.select_destination("Chicago")
            page.click_search()

        with allure.step("Assert validation error is shown"):
            assert page.is_error_visible(), (
                "Expected a validation error when departure == destination, "
                "but no error message was displayed."
            )

    @allure.story("Checkout Validation — Missing Name")
    @allure.title("Checkout form: missing name shows validation error")
    @pytest.mark.negative
    def test_checkout_missing_name_shows_error(self, driver) -> None:
        """
        Negative test: submitting checkout without a name should trigger
        the client-side validation error, keeping the user on the checkout page.
        """
        with allure.step("Navigate to checkout page"):
            purchase = _navigate_to_checkout(driver)

        with allure.step("Fill form with missing name"):
            purchase.populate_passenger_form(INVALID_PASSENGER_DATA_MISSING_NAME)

        with allure.step("Submit form"):
            purchase.submit_order()

        with allure.step("Assert error is shown or page stays on checkout"):
            current_url = driver.current_url
            error_shown = purchase.is_error_visible()
            on_checkout  = "checkout" in current_url.lower()

            assert error_shown or on_checkout, (
                "Expected form validation to prevent submission with a missing name, "
                f"but browser navigated to: {current_url}"
            )

    @allure.story("Checkout Validation — Invalid Email")
    @allure.title("Checkout form: invalid email shows validation error")
    @pytest.mark.negative
    def test_checkout_invalid_email_shows_error(self, driver) -> None:
        """Submitting with an email missing '@' should trigger client-side validation."""
        with allure.step("Navigate to checkout page"):
            purchase = _navigate_to_checkout(driver)

        with allure.step("Fill form with invalid email"):
            purchase.populate_passenger_form(INVALID_PASSENGER_DATA_BAD_EMAIL)

        with allure.step("Submit form"):
            purchase.submit_order()

        with allure.step("Assert validation error or user stays on checkout"):
            error_shown = purchase.is_error_visible()
            on_checkout  = "checkout" in driver.current_url.lower()
            assert error_shown or on_checkout, (
                "Expected validation error for invalid email, "
                f"but navigated to: {driver.current_url}"
            )

    @allure.story("Checkout Validation — Short Card Number")
    @allure.title("Checkout form: card number < 13 digits shows validation error")
    @pytest.mark.negative
    def test_checkout_short_card_shows_error(self, driver) -> None:
        """Submitting with a 4-digit card number should trigger the card validation."""
        with allure.step("Navigate to checkout page"):
            purchase = _navigate_to_checkout(driver)

        with allure.step("Fill form with too-short card number"):
            purchase.populate_passenger_form(INVALID_PASSENGER_DATA_SHORT_CARD)

        with allure.step("Submit form"):
            purchase.submit_order()

        with allure.step("Assert validation error or user stays on checkout"):
            error_shown = purchase.is_error_visible()
            on_checkout  = "checkout" in driver.current_url.lower()
            assert error_shown or on_checkout, (
                "Expected validation error for short card number, "
                f"but navigated to: {driver.current_url}"
            )

    @allure.story("Direct URL Access")
    @allure.title("Direct access to checkout.html without prior flight selection")
    @pytest.mark.negative
    def test_direct_checkout_access(self, driver) -> None:
        """
        Access checkout.html directly without selecting a flight.

        Expected behaviour: the page renders gracefully with a fallback
        message (no crash, no 500 error). The app reads sessionStorage which
        is empty, so it shows a 'No flight selected' state.
        """
        from config.config import cfg

        with allure.step("Navigate directly to checkout.html"):
            driver.get(cfg.base_url + "/checkout.html")

        with allure.step("Assert no server error in page title"):
            title = driver.title
            assert "500" not in title, (
                f"Server returned a 500 error on direct checkout access. Title: '{title}'"
            )
            assert len(driver.page_source) > 100, (
                "Checkout page appears blank on direct access."
            )

        logger.info("Direct checkout access handled gracefully. Title: '%s'", title)
