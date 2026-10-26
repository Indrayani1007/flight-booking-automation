"""
Test data payloads for BlazeDemo regression suite.

Centralised data store for:
- Valid passenger / billing profiles.
- Route matrix used in parameterised tests.
- Combined booking payloads for E2E tests.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Passenger / billing profiles
# ---------------------------------------------------------------------------

VALID_PASSENGER_DATA: Dict[str, str] = {
    "name":                "John Doe",
    "address":             "123 Automation Lane",
    "city":                "San Francisco",
    "state":               "California",
    "zip_code":            "94105",
    "card_type":           "Visa",
    "credit_card_number":  "4111111111111111",
    "credit_card_month":   "12",
    "credit_card_year":    "2027",
    "name_on_card":        "JOHN DOE",
    "remember_me":         False,
}

# Partial data — name and address omitted (used in boundary / negative tests)
PARTIAL_PASSENGER_DATA: Dict[str, str] = {
    "name":                "",
    "address":             "",
    "city":                "New York",
    "state":               "New York",
    "zip_code":            "10001",
    "card_type":           "Visa",
    "credit_card_number":  "4111111111111111",
    "credit_card_month":   "06",
    "credit_card_year":    "2026",
    "name_on_card":        "",
}

# ---------------------------------------------------------------------------
# Route matrix — (departure, destination) tuples
# ---------------------------------------------------------------------------

ROUTE_MATRIX: List[Tuple[str, str]] = [
    ("Boston",     "London"),
    ("Portland",   "Berlin"),
    ("San Diego",  "Rome"),
]

# Primary E2E route
E2E_ROUTE: Tuple[str, str] = ("Paris", "Buenos Aires")

# ---------------------------------------------------------------------------
# Combined booking payloads (route + passenger)
# ---------------------------------------------------------------------------

BOOKING_PAYLOADS: List[Dict] = [
    {
        "route":     E2E_ROUTE,
        "passenger": VALID_PASSENGER_DATA,
        "label":     "Paris_to_BuenosAires_Visa",
    },
]
