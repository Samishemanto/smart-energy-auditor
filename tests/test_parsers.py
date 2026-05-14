"""Unit tests for bill parsers and provider detection."""
import pytest
from backend.bill_parser import detect_provider, parse_bill


# ─── Provider detection ────────────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ("Your Scottish Power electricity bill for January 2024", "Scottish Power"),
    ("britishgas.co.uk — Your account summary", "British Gas"),
    ("Octopus Energy Ltd — Monthly statement", "Octopus Energy"),
    ("E.ON Next Energy — welcome to your bill", "E.ON Next"),
    ("npower UK — Your electricity statement", "nPower"),
    ("EDF Energy — Your bill is ready", "EDF Energy"),
    ("OVO Energy — here is your bill", "OVO Energy"),
    ("Shell Energy — monthly statement", "Shell Energy"),
    ("Random utility company", "Unknown"),
])
def test_detect_provider(text, expected):
    assert detect_provider(text) == expected


# ─── Amount extraction ────────────────────────────────────────────────────────

def test_parse_amount_due():
    text = "British Gas\nTotal amount due: £87.43\nPayment by direct debit"
    result = parse_bill(text)
    assert result["amount_due"] == pytest.approx(87.43, abs=0.01)


def test_parse_amount_please_pay():
    text = "Octopus Energy\nPlease pay £124.50 by 15 March 2024"
    result = parse_bill(text)
    assert result["amount_due"] == pytest.approx(124.50, abs=0.01)


# ─── Usage extraction ─────────────────────────────────────────────────────────

def test_parse_usage_kwh():
    text = "Scottish Power\nElectricity used: 342 kWh\nAmount due: £76.20"
    result = parse_bill(text)
    assert result["usage_kwh"] == 342


def test_parse_usage_units():
    text = "British Gas\nUnits used: 410 kWh this period\nTotal due £95.00"
    result = parse_bill(text)
    assert result["usage_kwh"] == 410


# ─── Date extraction ──────────────────────────────────────────────────────────

def test_parse_bill_date_long():
    text = "British Gas\nBill date: 15 March 2024\nAmount due £80.00"
    result = parse_bill(text)
    assert result["bill_date"] == "15 March 2024"


def test_parse_bill_date_short():
    text = "Octopus Energy\nStatement date: 20 Jan 2024\nTotal £65.00"
    result = parse_bill(text)
    assert result["bill_date"] is not None


# ─── Unit rate & standing charge ──────────────────────────────────────────────

def test_parse_unit_rate():
    text = "British Gas\nUnit rate: 24.50p per kWh\nAmount due £80.00"
    result = parse_bill(text)
    assert result["unit_rate"] == pytest.approx(24.50, abs=0.1)


def test_parse_standing_charge():
    text = "British Gas\nStanding charge: 61.0p per day\nAmount due £80.00"
    result = parse_bill(text)
    assert result["standing_charge"] == pytest.approx(61.0, abs=1.0)


# ─── Carbon calculation ───────────────────────────────────────────────────────

def test_carbon_calculated_from_kwh():
    text = "Scottish Power\nElectricity used: 500 kWh\nAmount due £110.00"
    result = parse_bill(text)
    if result["usage_kwh"]:
        assert result["carbon_kg"] == pytest.approx(500 * 0.197, abs=0.1)


# ─── Provider field set correctly ─────────────────────────────────────────────

def test_parse_sets_provider():
    text = "Octopus Energy Ltd\nUsage: 300 kWh\nTotal £72.00"
    result = parse_bill(text)
    assert result["provider"] == "Octopus Energy"


def test_parse_unknown_provider_fallback():
    text = "Some Random Energy Company\nUsage: 300 kWh\nTotal £72.00"
    result = parse_bill(text)
    assert result["provider"] == "Unknown"
    assert isinstance(result, dict)


# ─── Robustness ───────────────────────────────────────────────────────────────

def test_parse_empty_text():
    result = parse_bill("")
    assert isinstance(result, dict)
    assert result["provider"] == "Unknown"


def test_parse_no_numbers():
    result = parse_bill("British Gas — no numeric data here at all")
    assert result["provider"] == "British Gas"
    assert result.get("amount_due") is None
    assert result.get("usage_kwh") is None


def test_parse_multiple_amounts_picks_first_due():
    text = "British Gas\nUnit charge £45.00\nStanding charge £18.50\nTotal amount due £63.50"
    result = parse_bill(text)
    # Should pick the "amount due" one, not the first £ it finds
    assert result["amount_due"] == pytest.approx(63.50, abs=0.01)
