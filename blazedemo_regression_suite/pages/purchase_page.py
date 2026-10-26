"""
purchase_page.py — SkyBook Checkout Page Object.

Maps to: http://localhost:8000/checkout.html

Responsibilities:
    - Populate passenger details (name, email).
    - Populate payment information (card number, expiry, CVV).
    - Read the fare summary panel values for assertion.
    - Submit the checkout form.

Design Pattern — Field Map:
    Form fields are populated via a Python dict (the "field map" pattern).
    This makes the test data layer (booking_payloads.py) the single source
    of truth for passenger data, and allows the same form-filling logic to
    handle any combination of fields without conditional branching.
"""

from __future__ import annotations

import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class PurchasePage(BasePage):
    """
    Page Object representing the SkyBook checkout/purchase page.
    """

    # ── Locators ──────────────────────────────────────────────────────────────

    _PASSENGER_NAME  = (By.CSS_SELECTOR, "[data-testid='passenger-name']")
    _PASSENGER_EMAIL = (By.CSS_SELECTOR, "[data-testid='passenger-email']")
    _CC_NUMBER       = (By.CSS_SELECTOR, "[data-testid='cc-number']")
    _CC_EXPIRY       = (By.CSS_SELECTOR, "[data-testid='cc-expiry']")
    _CC_CVV          = (By.CSS_SELECTOR, "[data-testid='cc-cvv']")
    _CONFIRM_BTN     = (By.CSS_SELECTOR, "[data-testid='confirm-booking-btn']")
    _ERROR_BANNER    = (By.ID, "checkout-error")
    _CHECKOUT_TOTAL  = (By.CSS_SELECTOR, "[data-testid='checkout-total']")

    # Expose locators for negative tests that need to call clear_field()
    name_locator      = _PASSENGER_NAME
    cc_number_locator = _CC_NUMBER

    # ── Page readiness ────────────────────────────────────────────────────────

    def wait_for_page_load(self) -> "PurchasePage":
        """
        Wait until the checkout form and fare summary are rendered.

        The fare summary is populated by JavaScript after the page loads
        (reading from sessionStorage), so we wait for the confirm button
        to appear, which signals the JS has run.
        """
        self.wait_for_visible(self._CONFIRM_BTN)
        logger.info("PurchasePage loaded and ready")
        return self

    # ── Form population ───────────────────────────────────────────────────────

    def populate_passenger_form(self, data: dict) -> "PurchasePage":
        """
        Fill all form fields from the provided data dictionary.

        Field map keys (all optional — missing keys are skipped):
            "name"    → passenger full name
            "email"   → passenger email address
            "cc_num"  → credit card number (digits; auto-formatted)
            "cc_exp"  → expiry in MM/YY format
            "cc_cvv"  → 3 or 4-digit CVV

        Args:
            data: Dict of field values from test_data/booking_payloads.py.
        """
        self.wait_for_page_load()

        field_map = {
            "name":   self._PASSENGER_NAME,
            "email":  self._PASSENGER_EMAIL,
            "cc_num": self._CC_NUMBER,
            "cc_exp": self._CC_EXPIRY,
            "cc_cvv": self._CC_CVV,
        }

        for key, locator in field_map.items():
            value = data.get(key)
            if value is None:
                continue  # Skip optional fields not present in the payload
            self.type_text(locator, str(value))
            logger.debug("  Filled field '%s' = '%s'", key, value)

        logger.info("Passenger form populated with %d field(s)", len(data))
        return self

    def submit_order(self) -> None:
        """
        Click 'Confirm Booking' to submit the checkout form.

        After a successful submission, the browser navigates to confirmation.html.
        """
        self.click(self._CONFIRM_BTN)
        logger.info("Checkout form submitted")

    # ── Read-only accessors ───────────────────────────────────────────────────

    def get_total_amount(self) -> str:
        """
        Return the total amount string from the fare summary panel.

        Returns the raw text including the currency symbol (e.g., "$614.35")
        so callers can perform both format and value assertions.
        """
        return self.get_text(self._CHECKOUT_TOTAL)

    def get_error_message(self) -> str:
        """Return the text of the checkout error banner (used in negative tests)."""
        return self.get_text(self._ERROR_BANNER)

    def is_error_visible(self) -> bool:
        """Return True if the checkout error banner is currently shown."""
        try:
            el = self.wait_for_visible(self._ERROR_BANNER, timeout=3)
            return el.is_displayed()
        except Exception:
            return False
