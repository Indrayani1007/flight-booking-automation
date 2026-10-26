"""
booking_payloads.py — Parameterized Test Data for SkyBook Regression Suite.

Academic Purpose:
    Separating test data from test logic is a key principle of the Page Object
    Model pattern.  When the application's data (routes, passenger details) changes,
    only this file needs updating — the test logic remains untouched.

    This module defines:
      - Valid passenger data for the happy-path E2E test.
      - The default E2E route (Philadelphia → Buenos Aires).
      - A parameterized route matrix for multi-route smoke testing.
      - Invalid datasets for negative/boundary tests.
"""

from __future__ import annotations

import datetime

# ── Default E2E Route ─────────────────────────────────────────────────────────
# Used by the end-to-end happy-path test.
E2E_ROUTE = ("Philadelphia", "Buenos Aires")

# Travel date: tomorrow's date in YYYY-MM-DD format (always valid)
TOMORROW = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

# ── Valid Passenger Data ──────────────────────────────────────────────────────
# All fields required for a successful checkout form submission.
VALID_PASSENGER_DATA: dict = {
    "name":   "Alexandra Chen",
    "email":  "a.chen@testmail.com",
    "cc_num": "4111111111111111",  # Luhn-valid Visa test card
    "cc_exp": "12/27",
    "cc_cvv": "123",
}

# ── Route Matrix for Parameterized Tests ─────────────────────────────────────
# Each tuple: (departure_city, destination_city, expected_min_flights)
# Used in test_flight_search.py to verify multiple routes return results.
ROUTE_MATRIX = [
    ("Philadelphia",  "Buenos Aires", 1),
    ("New York",      "London",       1),
    ("Los Angeles",   "Tokyo",        1),
    ("Chicago",       "Paris",        1),
    ("Boston",        "Amsterdam",    1),
]

# ── Invalid/Boundary Datasets ────────────────────────────────────────────────
# Used in negative tests to verify form validation behaviour.
INVALID_PASSENGER_DATA_MISSING_NAME: dict = {
    "name":   "",                     # Empty name — should trigger validation
    "email":  "a.chen@testmail.com",
    "cc_num": "4111111111111111",
    "cc_exp": "12/27",
    "cc_cvv": "123",
}

INVALID_PASSENGER_DATA_BAD_EMAIL: dict = {
    "name":   "Test User",
    "email":  "not-an-email",         # Missing @ — should trigger validation
    "cc_num": "4111111111111111",
    "cc_exp": "12/27",
    "cc_cvv": "123",
}

INVALID_PASSENGER_DATA_SHORT_CARD: dict = {
    "name":   "Test User",
    "email":  "test@example.com",
    "cc_num": "1234",                 # Too short — should trigger validation
    "cc_exp": "12/27",
    "cc_cvv": "123",
}
