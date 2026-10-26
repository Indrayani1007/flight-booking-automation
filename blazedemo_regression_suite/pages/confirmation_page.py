"""
ConfirmationPage — BlazeDemo post-purchase confirmation page.

Extracts booking ID, status, and total amount from the summary table.

URL: https://blazedemo.com/confirmation.php

BlazeDemo confirmation table structure (verified via live DOM inspection):
  <table class="table">
    <tbody>
      <tr><td>Id</td><td>2</td></tr>
      <tr><td>Status</td><td>PendingCapture</td></tr>
      <tr><td>Amount</td><td>$ 433.79</td></tr>
      <tr><td>Tax</td><td>$ 54.22</td></tr>
      <tr><td>Total Amount</td><td>$ 487.01</td></tr>
      <tr><td>Airline</td><td>United Airlines</td></tr>
      <tr><td>Confirmation Code</td><td>GHU778</td></tr>
    </tbody>
  </table>
"""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage
from utilities.logger import get_logger

logger = get_logger(__name__)


class ConfirmationPage(BasePage):
    """
    Page Object for the booking confirmation page.

    Provides typed accessors for each data row in the confirmation table.
    Uses presence-based waits (not visibility) since the table cells are
    technically visible but the Selenium visibility check can be flaky on
    table elements in older Bootstrap layouts.
    """

    # ------------------------------------------------------------------
    # Locators — XPath targeting specific table rows by their label cell
    # Verified against live BlazeDemo confirmation page DOM.
    # ------------------------------------------------------------------

    # Booking ID / confirmation number
    _CONFIRMATION_ID  = (By.XPATH, "//td[normalize-space(text())='Id']/following-sibling::td[1]")

    # Booking status (e.g. "PendingCapture")
    _STATUS           = (By.XPATH, "//td[normalize-space(text())='Status']/following-sibling::td[1]")

    # Amount (first amount row)
    _AMOUNT           = (By.XPATH, "//td[normalize-space(text())='Amount']/following-sibling::td[1]")

    # Confirmation code (alternative unique identifier)
    _CONFIRMATION_CODE = (By.XPATH, "//td[normalize-space(text())='Confirmation Code']/following-sibling::td[1]")

    # Page heading — BlazeDemo uses an h1 on the confirmation page
    _PAGE_HEADING     = (By.CSS_SELECTOR, "h1, .hero-unit h2, div.container h2")

    # Table anchor — wait for this first to ensure page is loaded
    _TABLE_ANCHOR     = (By.CSS_SELECTOR, "table.table")

    # ------------------------------------------------------------------
    # Constructor
    # ------------------------------------------------------------------

    def __init__(self, driver: WebDriver) -> None:
        super().__init__(driver)
        # Wait for the table to appear before any accessor is called
        self._wait_for_table()

    def _wait_for_table(self) -> None:
        """Block until the confirmation table is present in the DOM."""
        try:
            self.wait_for_presence(self._TABLE_ANCHOR)
            logger.debug("Confirmation table detected in DOM")
        except Exception as exc:
            logger.warning("Confirmation table wait failed: %s", exc)

    # ------------------------------------------------------------------
    # Internal helper — use presence, not visibility, for table cells
    # ------------------------------------------------------------------

    def _get_cell_text(self, locator) -> str:
        """Return text of a table cell located by XPath, using presence wait."""
        element = self.wait_for_presence(locator)
        return element.text.strip()

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_confirmation_id(self) -> str:
        """
        Return the alphanumeric booking ID from the confirmation table.

        Returns:
            Non-empty string (e.g. ``"2"`` or ``"GHU778"``).
        """
        conf_id = self._get_cell_text(self._CONFIRMATION_ID)
        logger.info("Confirmation ID: %s", conf_id)
        return conf_id

    def get_booking_status(self) -> str:
        """
        Return the booking status (e.g. ``"PendingCapture"``).
        """
        status = self._get_cell_text(self._STATUS)
        logger.info("Booking status: %s", status)
        return status

    def get_total_amount(self) -> str:
        """
        Return the raw amount string (e.g. ``"$ 433.79"``).
        """
        amount = self._get_cell_text(self._AMOUNT)
        logger.info("Total amount: %s", amount)
        return amount

    def get_confirmation_code(self) -> str:
        """Return the airline confirmation code (e.g. ``"GHU778"``)."""
        code = self._get_cell_text(self._CONFIRMATION_CODE)
        logger.info("Confirmation code: %s", code)
        return code

    def get_heading(self) -> str:
        """Return the first heading text on the confirmation page."""
        try:
            return self._get_cell_text(self._PAGE_HEADING)
        except Exception:
            # Fallback: return page title
            return self.driver.title

    def is_booking_confirmed(self) -> bool:
        """
        Return True if a confirmation ID is present and non-empty.
        """
        try:
            conf_id = self.get_confirmation_id()
            return bool(conf_id)
        except Exception:  # noqa: BLE001
            return False
