"""
confirmation_page.py — SkyBook Booking Confirmation Page Object.

Maps to: http://localhost:8000/confirmation.html

Responsibilities:
    - Read the booking reference number.
    - Read the booking status badge.
    - Read passenger name, airline, route, flight number, date, and total amount.
    - Provide assertion-ready accessors for the E2E test.

Locator Strategy:
    Uses ``data-testid`` attributes for all fields. This pattern is robust
    against UI redesigns because test IDs are semantically meaningful and
    explicitly maintained for automation, unlike CSS class names which often
    change for visual reasons.
"""

from __future__ import annotations

import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class ConfirmationPage(BasePage):
    """
    Page Object representing the SkyBook booking confirmation page.
    """

    # ── Locators ──────────────────────────────────────────────────────────────

    _BOOKING_REF     = (By.CSS_SELECTOR, "[data-testid='booking-reference']")
    _BOOKING_STATUS  = (By.CSS_SELECTOR, "[data-testid='booking-status']")
    _PASSENGER_NAME  = (By.CSS_SELECTOR, "[data-testid='passenger-name']")
    _AIRLINE_NAME    = (By.CSS_SELECTOR, "[data-testid='airline-name']")
    _ROUTE           = (By.CSS_SELECTOR, "[data-testid='route']")
    _FLIGHT_NUMBER   = (By.CSS_SELECTOR, "[data-testid='flight-number']")
    _TRAVEL_DATE     = (By.CSS_SELECTOR, "[data-testid='travel-date']")
    _PASSENGER_COUNT = (By.CSS_SELECTOR, "[data-testid='passenger-count']")
    _TOTAL_AMOUNT    = (By.CSS_SELECTOR, "[data-testid='total-amount']")
    _NEW_SEARCH_BTN  = (By.CSS_SELECTOR, "a[href='index.html']")

    # ── Page readiness ────────────────────────────────────────────────────────

    def wait_for_confirmation(self) -> "ConfirmationPage":
        """
        Wait until the booking reference element is populated with a value.

        The confirmation page is rendered by JavaScript reading from sessionStorage,
        so we must wait for the DOM element to contain actual data before asserting.
        """
        # Wait for the booking reference to be visible and non-empty
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        WebDriverWait(self.driver, 15).until(
            lambda d: d.find_element(*self._BOOKING_REF).text.strip() not in ("", "—")
        )
        logger.info("ConfirmationPage loaded — reference populated")
        return self

    # ── Read-only accessors ───────────────────────────────────────────────────

    def get_confirmation_id(self) -> str:
        """
        Return the booking reference number (e.g., 'SKY-A3BK9R').

        This is the primary assertion point for the E2E test — a non-empty
        reference confirms the booking flow completed successfully end-to-end.
        """
        self.wait_for_confirmation()
        ref = self.get_text(self._BOOKING_REF)
        logger.info("Booking reference: %s", ref)
        return ref

    def get_booking_status(self) -> str:
        """Return the booking status badge text (expected: 'CONFIRMED')."""
        return self.get_text(self._BOOKING_STATUS)

    def get_passenger_name(self) -> str:
        """Return the passenger name as shown on the confirmation."""
        return self.get_text(self._PASSENGER_NAME)

    def get_airline_name(self) -> str:
        """Return the airline name."""
        return self.get_text(self._AIRLINE_NAME)

    def get_route(self) -> str:
        """Return the route string (e.g., 'Philadelphia → Buenos Aires')."""
        return self.get_text(self._ROUTE)

    def get_total_amount(self) -> str:
        """
        Return the total charged amount as a string (e.g., '$614.35').

        The test should assert that this value matches the amount displayed
        on the checkout page, validating end-to-end price consistency.
        """
        return self.get_text(self._TOTAL_AMOUNT)

    def is_confirmed(self) -> bool:
        """
        Return True if the booking status is 'CONFIRMED'.

        Convenience method for the most common assertion in the E2E test.
        """
        return self.get_booking_status().upper() == "CONFIRMED"
