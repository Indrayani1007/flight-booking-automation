"""
test_e2e_booking.py — Full End-to-End Flight Booking Transaction Test.

Test Scenario:
    A user completes the entire SkyBook booking funnel:
    1. Opens the home page and searches for a flight.
    2. Waits for the 2-second async spinner and selects a flight.
    3. Fills in passenger and payment details.
    4. Confirms the booking.
    5. Asserts the confirmation page shows a valid reference number.

Why this test is valuable:
    Unit tests verify individual components in isolation. The E2E test verifies
    that ALL components work together correctly as an integrated system.
    This is the most representative test from the end-user's perspective and
    is the primary regression guard against breaking changes.
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
    TOMORROW,
    VALID_PASSENGER_DATA,
)
from utilities.logger import get_logger

logger = get_logger(__name__)


@allure.feature("End-to-End Booking")
@allure.story("Happy Path")
class TestE2EBooking:
    """Full end-to-end happy-path booking test."""

    @allure.title("Complete flight booking — search → select → checkout → confirm")
    @pytest.mark.e2e
    @pytest.mark.regression
    def test_e2e_successful_flight_booking(self, driver) -> None:
        """
        E2E Test: Complete the SkyBook flight booking funnel from start to finish.

        Steps:
            1. Navigate to home page.
            2. Select departure and destination cities.
            3. Set travel date and submit search.
            4. Wait for async results (2-second spinner).
            5. Select the first available flight.
            6. Fill in passenger and payment form.
            7. Confirm the booking.
            8. Assert the confirmation page displays a valid booking reference.
            9. Assert the booking status is "CONFIRMED".

        Allure Attachment:
            Each step is wrapped in ``allure.step`` so the Allure report
            shows a visual timeline of every action taken during the test.
        """
        departure, destination = E2E_ROUTE

        # ── STEP 1: Open home page ───────────────────────────────────────────
        with allure.step("Step 1: Open SkyBook home page"):
            logger.info("E2E: Opening home page")
            finder = FlightFinderPage(driver)
            finder.open()
            assert "SkyBook" in driver.title, (
                f"Home page not loaded. Title: '{driver.title}'"
            )

        # ── STEP 2: Select route and date ────────────────────────────────────
        with allure.step(f"Step 2: Select route {departure} → {destination}"):
            finder.select_departure(departure)
            finder.select_destination(destination)
            finder.set_travel_date(TOMORROW)
            logger.info("Route set: %s → %s on %s", departure, destination, TOMORROW)

        # ── STEP 3: Submit search ────────────────────────────────────────────
        with allure.step("Step 3: Submit flight search"):
            finder.click_search()
            logger.info("Search submitted — awaiting results page")

        # ── STEP 4: Wait for async spinner + select first flight ─────────────
        with allure.step("Step 4: Wait for loading spinner and select first flight"):
            reserve = ReservePage(driver)
            reserve.wait_for_results()  # Explicit wait: spinner disappears

            count = reserve.flight_count()
            assert count >= 1, (
                f"No flights returned for {departure} → {destination}. "
                "Verify the FLIGHTS dataset in webapp/static/app.js."
            )
            logger.info("Found %d flight(s) — selecting index 0", count)

            reserve.choose_flight_by_index(0)

        # ── STEP 5: Verify redirect to checkout page ─────────────────────────
        with allure.step("Step 5: Verify checkout page loaded"):
            purchase = PurchasePage(driver)
            purchase.wait_for_page_load()
            assert "checkout" in driver.current_url.lower(), (
                f"Expected to be on checkout.html but URL is: {driver.current_url}"
            )

        # ── STEP 6: Fill in passenger and payment form ───────────────────────
        with allure.step("Step 6: Fill passenger and payment details"):
            logger.info("Filling passenger form with test data")
            purchase.populate_passenger_form(VALID_PASSENGER_DATA)

        # ── STEP 7: Capture checkout total before confirming ─────────────────
        with allure.step("Step 7: Read checkout total for later comparison"):
            checkout_total = purchase.get_total_amount()
            logger.info("Checkout total: %s", checkout_total)
            assert checkout_total.startswith("$"), (
                f"Checkout total does not start with '$': '{checkout_total}'. "
                "The fare summary may not have rendered correctly."
            )

        # ── STEP 8: Submit the order ─────────────────────────────────────────
        with allure.step("Step 8: Confirm booking"):
            purchase.submit_order()
            logger.info("Booking submitted")

        # ── STEP 9: Verify confirmation page ─────────────────────────────────
        with allure.step("Step 9: Verify confirmation page and booking reference"):
            confirmation = ConfirmationPage(driver)
            conf_id = confirmation.get_confirmation_id()

            assert conf_id, (
                "Booking confirmation ID is empty. The E2E flow did not complete successfully."
            )
            assert conf_id.startswith("SKY-"), (
                f"Confirmation ID format unexpected: '{conf_id}'. "
                "Expected format: 'SKY-XXXXXX'."
            )

            logger.info("✓ Booking confirmed with reference: %s", conf_id)
            allure.attach(conf_id, name="Booking Reference", attachment_type=allure.attachment_type.TEXT)

        with allure.step("Step 10: Verify booking status is CONFIRMED"):
            assert confirmation.is_confirmed(), (
                f"Booking status is not 'CONFIRMED'. Got: '{confirmation.get_booking_status()}'."
            )

        with allure.step("Step 11: Verify passenger name on confirmation"):
            conf_name = confirmation.get_passenger_name()
            assert conf_name == VALID_PASSENGER_DATA["name"], (
                f"Passenger name mismatch on confirmation. "
                f"Expected: '{VALID_PASSENGER_DATA['name']}', Got: '{conf_name}'."
            )

        with allure.step("Step 12: Verify total amount matches checkout amount"):
            conf_total = confirmation.get_total_amount()
            assert conf_total == checkout_total, (
                f"Price discrepancy: checkout showed '{checkout_total}' "
                f"but confirmation shows '{conf_total}'."
            )

        logger.info("✅ E2E booking test PASSED — Reference: %s, Total: %s", conf_id, conf_total)
