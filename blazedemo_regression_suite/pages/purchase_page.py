"""
PurchasePage — BlazeDemo passenger and billing checkout form.

Populates all passenger and credit-card fields, then submits the order.

URL: https://blazedemo.com/purchase.php
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class PurchasePage(BasePage):
    """
    Page Object for the passenger & billing checkout page.

    All locators use the ``id`` attribute from the BlazeDemo form so they
    are insensitive to DOM restructuring outside those elements.
    """

    PAGE_URL: str = "/purchase.php"

    # ------------------------------------------------------------------
    # Locators — text inputs
    # ------------------------------------------------------------------

    _INPUT_NAME     = (By.ID, "inputName")
    _ADDRESS        = (By.ID, "address")
    _CITY           = (By.ID, "city")
    _STATE          = (By.ID, "state")
    _ZIP_CODE       = (By.ID, "zipCode")
    _CARD_TYPE      = (By.ID, "cardType")        # <select>
    _CC_NUMBER      = (By.ID, "creditCardNumber")
    _CC_MONTH       = (By.ID, "creditCardMonth")
    _CC_YEAR        = (By.ID, "creditCardYear")
    _NAME_ON_CARD   = (By.ID, "nameOnCard")
    _REMEMBER_ME    = (By.ID, "rememberMe")      # checkbox

    _PURCHASE_BTN   = (By.CSS_SELECTOR, "input[type='submit']")

    # Page heading to confirm correct page
    _PAGE_HEADING   = (By.CSS_SELECTOR, "h2")

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------

    def __init__(self, driver: WebDriver) -> None:
        super().__init__(driver)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def populate_passenger_form(self, data: dict) -> "PurchasePage":
        """
        Populate all passenger and billing fields from a data dictionary.

        Expected keys (all strings unless noted):
        - ``name``           — Passenger full name
        - ``address``        — Street address
        - ``city``           — City
        - ``state``          — State
        - ``zip_code``       — Postal / ZIP code
        - ``card_type``      — Card type visible text (e.g. "Visa")
        - ``credit_card_number`` — Card number (digits only)
        - ``credit_card_month``  — Expiry month (MM)
        - ``credit_card_year``   — Expiry year (YYYY)
        - ``name_on_card``   — Name as printed on card
        - ``remember_me``    — (bool, optional) Check the "Remember me" checkbox

        Unrecognised keys are silently ignored.

        Args:
            data: Dictionary of passenger and billing details.

        Returns:
            Self for method chaining.
        """
        logger.info("Populating passenger form for: %s", data.get("name", "<unknown>"))

        field_map = {
            "name":                (self._fill_if_provided, self._INPUT_NAME),
            "address":             (self._fill_if_provided, self._ADDRESS),
            "city":                (self._fill_if_provided, self._CITY),
            "state":               (self._fill_if_provided, self._STATE),
            "zip_code":            (self._fill_if_provided, self._ZIP_CODE),
            "credit_card_number":  (self._fill_if_provided, self._CC_NUMBER),
            "credit_card_month":   (self._fill_if_provided, self._CC_MONTH),
            "credit_card_year":    (self._fill_if_provided, self._CC_YEAR),
            "name_on_card":        (self._fill_if_provided, self._NAME_ON_CARD),
        }

        for key, (action, locator) in field_map.items():
            value = data.get(key)
            if value is not None:
                action(locator, str(value))

        # Card type is a select element
        if card_type := data.get("card_type"):
            self.select_by_text(self._CARD_TYPE, card_type)

        # Remember Me checkbox
        if data.get("remember_me"):
            self._check_checkbox(self._REMEMBER_ME)

        return self

    def _fill_if_provided(self, locator, value: str) -> None:
        """Helper: only call fill() when value is a non-empty string."""
        if value:
            self.fill(locator, value)

    def _check_checkbox(self, locator) -> None:
        """Ensure a checkbox is checked (idempotent)."""
        element = self.wait_for_presence(locator)
        if not element.is_selected():
            element.click()

    def clear_field(self, locator) -> None:
        """
        Explicitly clear a form field — used in negative test scenarios.

        Args:
            locator: ``(By.*, selector)`` tuple of the field to clear.
        """
        element = self.wait_for_visibility(locator)
        element.clear()

    def submit_order(self) -> None:
        """
        Click the "Purchase Flight" submit button.

        After clicking, the browser navigates to the confirmation page;
        callers should instantiate :class:`~pages.confirmation_page.ConfirmationPage`.
        """
        logger.info("Submitting purchase order")
        self.click(self._PURCHASE_BTN)

    # ------------------------------------------------------------------
    # Convenience properties for negative tests
    # ------------------------------------------------------------------

    @property
    def name_locator(self):
        return self._INPUT_NAME

    @property
    def address_locator(self):
        return self._ADDRESS

    @property
    def city_locator(self):
        return self._CITY

    @property
    def state_locator(self):
        return self._STATE

    @property
    def zip_code_locator(self):
        return self._ZIP_CODE

    @property
    def cc_number_locator(self):
        return self._CC_NUMBER

    def get_heading(self) -> str:
        """Return the checkout page heading."""
        return self.get_text(self._PAGE_HEADING)
