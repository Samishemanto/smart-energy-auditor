from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    google_sub = Column(String, unique=True, nullable=True, index=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    budget_monthly_gbp = Column(Float, nullable=True)
    budget_monthly_kwh = Column(Integer, nullable=True)
    email_alerts = Column(Boolean, default=False, nullable=False)
    goal_reduction_pct = Column(Float, nullable=True)      # e.g. 10.0 = reduce by 10%
    goal_baseline_kwh  = Column(Float, nullable=True)      # avg kWh when goal was set
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)               # FK to users.id (soft ref)
    filename = Column(String, nullable=False)
    provider = Column(String, nullable=False, default="Unknown")
    account_number = Column(String, nullable=True)
    bill_date = Column(String, nullable=True)
    due_date = Column(String, nullable=True)
    amount_due = Column(Float, nullable=True)
    usage_kwh = Column(Integer, nullable=True)
    standing_charge = Column(Float, nullable=True)   # pence per day
    unit_rate = Column(Float, nullable=True)          # pence per kWh
    tariff_name = Column(String, nullable=True)
    meter_serial = Column(String, nullable=True)
    carbon_kg = Column(Float, nullable=True)          # kg CO₂ (usage × 0.197)
    raw_text = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
