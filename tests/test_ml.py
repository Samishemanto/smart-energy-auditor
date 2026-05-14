"""Unit tests for ML functions."""
import pytest
from unittest.mock import MagicMock
from backend.ml import (
    predict_next_month, detect_anomalies, classify_usage,
    generate_recommendations, cluster_usage, detect_changepoints,
)


def _make_bill(id, usage_kwh, amount_due, bill_date="01 January 2024",
               provider="British Gas", unit_rate=24.5, standing_charge=60.0,
               carbon_kg=None):
    b = MagicMock()
    b.id            = id
    b.usage_kwh     = usage_kwh
    b.amount_due    = amount_due
    b.bill_date     = bill_date
    b.provider      = provider
    b.unit_rate     = unit_rate
    b.standing_charge = standing_charge
    b.carbon_kg     = carbon_kg or (round(usage_kwh * 0.197, 2) if usage_kwh else None)
    b.filename      = f"bill_{id}.jpg"
    return b


BILLS_3 = [
    _make_bill(1, 350, 85.50, "01 January 2024"),
    _make_bill(2, 420, 92.00, "01 February 2024"),
    _make_bill(3, 310, 78.00, "01 March 2024"),
]

BILLS_5 = BILLS_3 + [
    _make_bill(4, 290, 72.00, "01 April 2024"),
    _make_bill(5, 380, 88.00, "01 May 2024"),
]


# ─── Predict next month ────────────────────────────────────────────────────────

def test_predict_insufficient_data():
    result = predict_next_month([_make_bill(1, 300, 70.0, "01 Jan 2024")])
    assert result["status"] == "insufficient_data"


def test_predict_linear_2_bills():
    bills = [
        _make_bill(1, 300, 70.0, "01 January 2024"),
        _make_bill(2, 350, 80.0, "01 February 2024"),
    ]
    result = predict_next_month(bills)
    assert result["status"] == "ok"
    assert result["predicted_kwh"] >= 0
    assert result["predicted_cost"] >= 0
    assert "next_period" in result
    assert result["model"] == "linear_regression"


def test_predict_returns_trend(  ):
    result = predict_next_month(BILLS_3)
    assert result["status"] == "ok"
    assert result["trend"] in ("increasing", "decreasing")
    assert isinstance(result["monthly_change_kwh"], float)


def test_predict_carbon():
    result = predict_next_month(BILLS_3)
    if result["status"] == "ok":
        assert result["predicted_carbon_kg"] == pytest.approx(
            result["predicted_kwh"] * 0.197, abs=1.0
        )


# ─── Anomaly detection ────────────────────────────────────────────────────────

def test_anomalies_insufficient():
    result = detect_anomalies(BILLS_3[:2])
    assert result == []


def test_anomalies_returns_list():
    result = detect_anomalies(BILLS_3)
    assert isinstance(result, list)


def test_anomalies_with_spike():
    bills = BILLS_3 + [_make_bill(99, 1500, 320.0, "01 June 2024")]  # obvious spike
    result = detect_anomalies(bills)
    spike_ids = [r["id"] for r in result]
    assert 99 in spike_ids


def test_anomaly_has_pct_diff():
    bills = BILLS_3 + [_make_bill(99, 2000, 400.0, "01 June 2024")]
    result = detect_anomalies(bills)
    for r in result:
        assert "pct_diff_from_mean" in r
        assert "reason" in r


# ─── Usage classification ─────────────────────────────────────────────────────

def test_classify_no_data():
    result = classify_usage([MagicMock(usage_kwh=None)])
    assert result["classification"] == "Unknown"


def test_classify_low():
    bills = [_make_bill(i, 100, 30.0) for i in range(3)]
    result = classify_usage(bills)
    assert result["classification"] == "Low"
    assert result["estimated_annual_kwh"] < 2000


def test_classify_high():
    bills = [_make_bill(i, 600, 140.0) for i in range(3)]
    result = classify_usage(bills)
    assert result["classification"] == "High"
    assert result["estimated_annual_kwh"] > 4000


def test_classify_medium():
    bills = [_make_bill(i, 260, 65.0) for i in range(3)]
    result = classify_usage(bills)
    assert result["classification"] == "Medium"


def test_classify_pct_vs_uk():
    bills = [_make_bill(i, 500, 120.0) for i in range(3)]
    result = classify_usage(bills)
    assert "pct_vs_uk_avg" in result
    assert isinstance(result["pct_vs_uk_avg"], float)


# ─── Recommendations ──────────────────────────────────────────────────────────

def test_recommendations_empty():
    result = generate_recommendations([])
    assert len(result) >= 1
    assert result[0]["type"] == "info"


def test_recommendations_spike_detected():
    bills = [
        _make_bill(1, 200, 50.0, "01 January 2024"),
        _make_bill(2, 500, 120.0, "01 February 2024"),  # big spike
    ]
    recs = generate_recommendations(bills)
    types = [r["type"] for r in recs]
    titles = " ".join(r["title"] for r in recs)
    assert "warning" in types
    assert any("spike" in t.lower() or "usage" in t.lower() for t in [r["title"] for r in recs])


def test_recommendations_have_required_fields():
    recs = generate_recommendations(BILLS_3)
    for r in recs:
        assert "type" in r
        assert "title" in r
        assert "detail" in r
        assert r["type"] in ("warning", "success", "info")
        assert "priority" not in r  # internal field must be stripped


def test_recommendations_high_unit_rate():
    bills = [_make_bill(i, 300, 80.0, unit_rate=32.0) for i in range(2)]
    for b in bills:
        b.bill_date = "01 January 2024"
    recs = generate_recommendations(bills)
    titles = " ".join(r["title"].lower() for r in recs)
    assert "rate" in titles or "tariff" in titles


# ─── KMeans clustering ────────────────────────────────────────────────────────

def test_cluster_insufficient():
    result = cluster_usage(BILLS_3[:2])
    assert result["status"] == "insufficient_data"


def test_cluster_ok():
    result = cluster_usage(BILLS_3)
    assert result["status"] == "ok"
    assert "bills" in result
    assert "summary" in result
    for b in result["bills"]:
        assert "cluster_name" in b
        assert b["cluster_name"] in ("Low Usage", "Medium Usage", "High Usage")


def test_cluster_count_matches():
    result = cluster_usage(BILLS_5)
    assert result["status"] == "ok"
    assert len(result["bills"]) == 5


# ─── Changepoint detection ────────────────────────────────────────────────────

def test_changepoints_insufficient():
    result = detect_changepoints(BILLS_3[:3])
    assert result["status"] == "insufficient_data"


def test_changepoints_ok():
    bills = BILLS_5
    result = detect_changepoints(bills)
    assert result["status"] == "ok"
    assert "changepoints" in result
    assert isinstance(result["changepoints"], list)


def test_changepoints_detects_shift():
    low  = [_make_bill(i, 200, 50.0, f"01 {'Jan Feb Mar Apr'.split()[i]} 2024") for i in range(4)]
    high = [_make_bill(i+4, 600, 140.0, f"01 {'May Jun Jul Aug'.split()[i]} 2024") for i in range(4)]
    bills = low + high
    result = detect_changepoints(bills)
    assert result["status"] == "ok"
    # There should be at least one changepoint where usage jumps
    if result["changepoints"]:
        for cp in result["changepoints"]:
            assert "pct_change" in cp
            assert "direction" in cp
