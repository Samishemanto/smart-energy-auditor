"""API endpoint tests for Smart Energy Auditor."""
import io
import pytest


# ─── Health ───────────────────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ─── Auth ─────────────────────────────────────────────────────────────────────

def test_auth_me_no_token(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_auth_me_valid(client, auth_headers):
    r = client.get("/auth/me", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_auth_me_invalid_token(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer bad.token.here"})
    assert r.status_code == 401


# ─── Bills ────────────────────────────────────────────────────────────────────

def test_list_bills_empty(client, auth_headers):
    r = client.get("/bills", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_bills_with_data(client, auth_headers, sample_bills):
    r = client.get("/bills", headers=auth_headers)
    assert r.status_code == 200
    ids = [b["id"] for b in r.json()]
    for bill in sample_bills:
        assert bill.id in ids


def test_get_bill_by_id(client, auth_headers, sample_bills):
    bill_id = sample_bills[0].id
    r = client.get(f"/bills/{bill_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["id"] == bill_id
    assert r.json()["provider"] == "British Gas"


def test_get_bill_not_found(client, auth_headers):
    r = client.get("/bills/999999", headers=auth_headers)
    assert r.status_code == 404


def test_create_manual_bill(client, auth_headers):
    payload = {
        "provider": "Octopus Energy",
        "bill_date": "01 April 2024",
        "amount_due": 67.50,
        "usage_kwh": 280,
        "unit_rate": 22.0,
        "standing_charge": 55.0,
    }
    r = client.post("/bills/manual", json=payload, headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["provider"] == "Octopus Energy"
    assert data["usage_kwh"] == 280
    assert data["carbon_kg"] == pytest.approx(55.16, abs=0.1)  # 280 × 0.197


def test_patch_bill(client, auth_headers, sample_bills):
    bill_id = sample_bills[0].id
    r = client.patch(
        f"/bills/{bill_id}",
        json={"amount_due": 99.99, "provider": "Updated Provider"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["amount_due"] == 99.99
    assert r.json()["provider"] == "Updated Provider"


def test_patch_bill_not_found(client, auth_headers):
    r = client.patch("/bills/999999", json={"amount_due": 10.0}, headers=auth_headers)
    assert r.status_code == 404


def test_delete_bill(client, auth_headers, db, test_user):
    from database.models import Bill
    b = Bill(user_id=test_user.id, filename="temp.jpg", provider="Temp", carbon_kg=None)
    db.add(b)
    db.commit()
    db.refresh(b)

    r = client.delete(f"/bills/{b.id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["deleted"] == b.id

    r2 = client.get(f"/bills/{b.id}", headers=auth_headers)
    assert r2.status_code == 404


# ─── Stats ────────────────────────────────────────────────────────────────────

def test_stats(client, auth_headers, sample_bills):
    r = client.get("/stats", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total_bills"] >= 3
    assert data["total_spend"] > 0
    assert data["avg_monthly_kwh"] > 0
    assert "providers" in data


# ─── Upload validation ────────────────────────────────────────────────────────

def test_upload_wrong_type(client, auth_headers):
    fake_file = io.BytesIO(b"fake content")
    r = client.post(
        "/upload-bill",
        files={"file": ("test.txt", fake_file, "text/plain")},
        headers=auth_headers,
    )
    assert r.status_code == 415


def test_upload_too_large(client, auth_headers):
    big = io.BytesIO(b"x" * (21 * 1024 * 1024))
    r = client.post(
        "/upload-bill",
        files={"file": ("big.jpg", big, "image/jpeg")},
        headers=auth_headers,
    )
    assert r.status_code == 413


# ─── Budget ───────────────────────────────────────────────────────────────────

def test_get_budget_default(client, auth_headers):
    r = client.get("/budget", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "budget_monthly_gbp" in data
    assert "budget_monthly_kwh" in data
    assert "email_alerts" in data


def test_set_budget(client, auth_headers):
    r = client.put(
        "/budget",
        json={"budget_monthly_gbp": 100.0, "budget_monthly_kwh": 400, "email_alerts": False},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["budget_monthly_gbp"] == 100.0
    assert data["budget_monthly_kwh"] == 400


def test_budget_status(client, auth_headers, sample_bills):
    client.put(
        "/budget",
        json={"budget_monthly_gbp": 80.0, "budget_monthly_kwh": 300},
        headers=auth_headers,
    )
    r = client.get("/budget/status", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "cost_status" in data
    assert "kwh_status" in data
    assert data["cost_status"] in ("ok", "warning", "exceeded")


# ─── ML endpoints ─────────────────────────────────────────────────────────────

def test_ml_predictions_insufficient(client, auth_headers):
    r = client.get("/ml/predictions", headers=auth_headers)
    assert r.status_code == 200
    # May return insufficient_data if prior tests cleaned up bills


def test_ml_predictions_with_data(client, auth_headers, sample_bills):
    r = client.get("/ml/predictions", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    if data["status"] == "ok":
        assert "predicted_kwh" in data
        assert "predicted_cost" in data
        assert data["predicted_kwh"] >= 0


def test_ml_anomalies(client, auth_headers, sample_bills):
    r = client.get("/ml/anomalies", headers=auth_headers)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_ml_classify(client, auth_headers, sample_bills):
    r = client.get("/ml/classify", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["classification"] in ("Low", "Medium", "High")


def test_ml_recommendations(client, auth_headers, sample_bills):
    r = client.get("/ml/recommendations", headers=auth_headers)
    assert r.status_code == 200
    recs = r.json()
    assert isinstance(recs, list)
    assert len(recs) > 0
    for rec in recs:
        assert "type" in rec
        assert "title" in rec
        assert "detail" in rec
        assert rec["type"] in ("warning", "success", "info")


def test_ml_clusters(client, auth_headers, sample_bills):
    r = client.get("/ml/clusters", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "status" in data


def test_ml_changepoints(client, auth_headers, sample_bills):
    r = client.get("/ml/changepoints", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
