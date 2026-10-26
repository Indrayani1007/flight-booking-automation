"""
test_e2e_booking.py — Full end-to-end flight booking test.

Covers the complete user journey from home page through to booking
confirmation, including cheapest flight selection and confirmation
data assertions.
"""

from __future__ import annotations

import re

import pytest

from pages.confirmation_page import ConfirmationPage
from pages.flight_finder_page import FlightFinderPage
from pages.purchase_page import PurchasePage
from pages.reserve_page import ReservePage
from test_data.booking_payloads import E2E_ROUTE, VALID_PASSENGER_DATA
from utilities.logger import get_logger

logger = get_logger(__name__)


class TestE2EBooking:
    """End-to-end booking workflow tests."""

    @pytest.mark.e2e
    @pytest.mark.regression
    def test_e2e_successful_flight_booking(self, driver) -> None:
        """
        Full end-to-end test: Paris → Buenos Aires, cheapest flight,
        valid billing data, purchase, and confirmation assertions.

        Assertions:
        - Confirmation ID is a non-empty alphanumeric string.
        - Booking status is "PendingCapture".
        - Amount contains a numeric value (price consistency check).

        Steps:
        1. Open BlazeDemo home.
        2. Select Paris → Buenos Aires.
        3. Click "Find Flights".
        4. Identify and select the cheapest available flight.
        5. Populate the passenger / billing form with valid mock data.
        6. Click "Purchase Flight".
        7. Assert confirmation page heading, ID, status, and amount.
        """
        logger.info("=" * 60)
        logger.info("TEST: E2E flight booking — Paris → Buenos Aires")

        departure, destination = E2E_ROUTE

        # ----------------------------------------------------------------
        # Step 1–2: Navigate and select route
        # ----------------------------------------------------------------
        finder = FlightFinderPage(driver)
        finder.open()
        finder.select_route(departure, destination)

        # ----------------------------------------------------------------
        # Step 3: Search for flights
        # ----------------------------------------------------------------
        finder.click_find_flights()

        # ----------------------------------------------------------------
        # Step 4: Choose cheapest flight
        # ----------------------------------------------------------------
        reserve = ReservePage(driver)
        chosen_flight = reserve.choose_cheapest_flight()
        logger.info(
            "Chosen flight: %s @ %s",
            chosen_flight["airline"],
            chosen_flight["price_raw"],
        )

        # ----------------------------------------------------------------
        # Step 5: Fill passenger / billing form
        # ----------------------------------------------------------------
        purchase = PurchasePage(driver)
        purchase.populate_passenger_form(VALID_PASSENGER_DATA)

        # ----------------------------------------------------------------
        # Step 6: Submit order
        # ----------------------------------------------------------------
        purchase.submit_order()

        # ----------------------------------------------------------------
        # Step 7: Verify confirmation
        # ----------------------------------------------------------------
        confirmation = ConfirmationPage(driver)

        # 7a: Heading check
        heading = confirmation.get_heading()
        assert heading, "Confirmation page heading is empty."
        logger.info("Confirmation heading: '%s'", heading)

        # 7b: Confirmation ID — must be non-empty alphanumeric
        conf_id = confirmation.get_confirmation_id()
        assert conf_id, "Confirmation ID is empty."
        assert re.match(r"[A-Za-z0-9]+", conf_id), (
            f"Confirmation ID does not appear alphanumeric: '{conf_id}'"
        )
        logger.info("Confirmation ID: %s ✓", conf_id)

        # 7c: Status — must be "PendingCapture"
        status = confirmation.get_booking_status()
        assert status == "PendingCapture", (
            f"Expected booking status 'PendingCapture', got '{status}'"
        )
        logger.info("Booking status: %s ✓", status)

        # 7d: Amount — must contain a numeric value
        amount = confirmation.get_total_amount()
        assert amount, "Amount field is empty on confirmation page."
        numeric_match = re.search(r"\d+\.?\d*", amount.replace(",", ""))
        assert numeric_match, (
            f"Could not extract numeric value from amount: '{amount}'"
        )
        amount_float = float(numeric_match.group())
        assert amount_float > 0, f"Total amount is not positive: {amount_float}"
        logger.info("Total amount: %s (%.2f) ✓", amount, amount_float)

        logger.info("E2E booking test PASSED. Confirmation ID: %s", conf_id)
