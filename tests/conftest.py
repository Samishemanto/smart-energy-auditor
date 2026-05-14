"""Pytest configuration — sets up an in-memory SQLite DB and a test JWT token."""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Point to in-memory SQLite before importing app
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-minimum!!")
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id")
os.environ.setdefault("GOOGLE_CLIENT_SECRET", "test-client-secret")

from backend.app import app
from backend.db import get_db
from database.models import Base, User, Bill

_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_Session = sessionmaker(bind=_engine)

# Create tables immediately at import time so they exist for all test sessions
Base.metadata.create_all(bind=_engine)


def _override_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_db


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    # Tables already created above; this fixture ensures ordering for fixtures that depend on it
    yield


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=_engine)
    session = _Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture()
def test_user(db):
    user = User(email="test@example.com", name="Test User", google_sub="sub_123", is_admin=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    yield user
    db.delete(user)
    db.commit()


@pytest.fixture()
def auth_headers(test_user):
    from backend.auth import create_jwt
    token = create_jwt(test_user.id, test_user.email)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def client():
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture()
def sample_bills(db, test_user):
    bills = [
        Bill(user_id=test_user.id, filename="bill1.jpg", provider="British Gas",
             bill_date="01 January 2024", amount_due=85.50, usage_kwh=350,
             unit_rate=24.5, standing_charge=60.0, carbon_kg=68.95),
        Bill(user_id=test_user.id, filename="bill2.jpg", provider="British Gas",
             bill_date="01 February 2024", amount_due=92.00, usage_kwh=420,
             unit_rate=24.5, standing_charge=60.0, carbon_kg=82.74),
        Bill(user_id=test_user.id, filename="bill3.jpg", provider="British Gas",
             bill_date="01 March 2024", amount_due=78.00, usage_kwh=310,
             unit_rate=24.5, standing_charge=60.0, carbon_kg=61.07),
    ]
    for b in bills:
        db.add(b)
    db.commit()
    yield bills
    for b in bills:
        db.delete(b)
    db.commit()
