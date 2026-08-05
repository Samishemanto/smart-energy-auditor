from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any, Dict, List
import os

from dotenv import load_dotenv
load_dotenv()

from backend.db import engine, get_db
from database.models import Base, Bill, User
from backend.ocr import extract_text
from backend.bill_parser import parse_bill
from backend.ml import (
    predict_next_month, detect_anomalies, classify_usage,
    generate_recommendations, cluster_usage, detect_changepoints,
    predict_cost_gbr,
)
from backend.report import generate_pdf_report
from backend.auth import (
    get_google_auth_url, exchange_code_for_tokens, get_google_user_info,
    create_jwt, get_current_user, require_admin, STREAMLIT_URL, FRONTEND_URL, ADMIN_EMAIL,
)
from backend.email_alerts import send_spike_alert, send_weekly_summary, send_due_date_reminder

# ─── STARTUP ───────────────────────────────────────────────────────────────────

Base.metadata.create_all(bind=engine)


def _migrate_new_columns() -> None:
    import os
    db_url = os.getenv("DATABASE_URL", "sqlite")
    if not db_url.startswith("sqlite"):
        return  # PostgreSQL: create_all handles schema, no PRAGMA needed
    bill_cols = {
        "standing_charge": "FLOAT",
        "unit_rate": "FLOAT",
        "tariff_name": "VARCHAR",
        "meter_serial": "VARCHAR",
        "carbon_kg": "FLOAT",
        "uploaded_at": "DATETIME",
        "user_id": "INTEGER",
    }
    user_cols = {
        "is_admin": "BOOLEAN DEFAULT 0",
        "budget_monthly_gbp": "FLOAT",
        "budget_monthly_kwh": "INTEGER",
        "email_alerts": "BOOLEAN DEFAULT 0",
        "goal_reduction_pct": "FLOAT",
        "goal_baseline_kwh": "FLOAT",
    }
    with engine.connect() as conn:
        existing_bills = {row[1] for row in conn.execute(text("PRAGMA table_info(bills)"))}
        for col, dtype in bill_cols.items():
            if col not in existing_bills:
                conn.execute(text(f"ALTER TABLE bills ADD COLUMN {col} {dtype}"))

        existing_users = {row[1] for row in conn.execute(text("PRAGMA table_info(users)"))}
        for col, dtype in user_cols.items():
            if col not in existing_users:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {dtype}"))
        conn.commit()


_migrate_new_columns()

# ─── APP ───────────────────────────────────────────────────────────────────────

app = FastAPI(title="Smart Energy Auditor API", version="0.3.0")

_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://smart-energy-auditor.vercel.app",
    os.getenv("FRONTEND_URL", "https://smart-energy-auditor.vercel.app"),
    os.getenv("REACT_URL", "http://localhost:5173"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set(_ALLOWED_ORIGINS)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploaded_bills"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ─── SCHEMAS ───────────────────────────────────────────────────────────────────

class BillOut(BaseModel):
    id: int
    filename: str
    provider: str
    account_number: str | None = None
    bill_date: str | None = None
    due_date: str | None = None
    amount_due: float | None = None
    usage_kwh: int | None = None
    standing_charge: float | None = None
    unit_rate: float | None = None
    tariff_name: str | None = None
    meter_serial: str | None = None
    carbon_kg: float | None = None

    class Config:
        from_attributes = True


class UploadResponse(BillOut):
    extracted_text: str


class StatsOut(BaseModel):
    total_bills: int
    total_spend: float
    avg_monthly_kwh: float
    avg_monthly_cost: float
    total_carbon_kg: float
    providers: Dict[str, int]


class UserOut(BaseModel):
    id: int
    email: str
    name: str | None = None
    is_admin: bool = False

    class Config:
        from_attributes = True


class AdminUserOut(BaseModel):
    id: int
    email: str
    name: str | None = None
    is_admin: bool
    bill_count: int
    created_at: str | None = None

    class Config:
        from_attributes = True


# ─── PUBLIC ENDPOINTS ──────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "name": "Smart Energy Auditor API", "version": "0.3.0", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok", "version": "0.3.0"}


# ─── AUTH ENDPOINTS ────────────────────────────────────────────────────────────

@app.get("/auth/google")
def auth_google():
    return {"url": get_google_auth_url()}


@app.get("/auth/callback")
async def auth_callback(code: str, db: Session = Depends(get_db)):
    try:
        tokens = await exchange_code_for_tokens(code)
        user_info = await get_google_user_info(tokens["access_token"])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google auth failed: {e}")

    user = db.query(User).filter(User.google_sub == user_info["sub"]).first()
    if not user:
        is_admin = (user_info["email"] == ADMIN_EMAIL)
        user = User(
            email=user_info["email"],
            name=user_info.get("name", ""),
            google_sub=user_info["sub"],
            is_admin=is_admin,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif ADMIN_EMAIL and user.email == ADMIN_EMAIL and not user.is_admin:
        user.is_admin = True
        db.commit()

    token = create_jwt(user.id, user.email)
    return RedirectResponse(f"{FRONTEND_URL}?token={token}")


@app.get("/auth/me", response_model=UserOut)
def auth_me(current_user: User = Depends(get_current_user)):
    return current_user


# ─── PROTECTED ENDPOINTS ───────────────────────────────────────────────────────

@app.get("/stats", response_model=StatsOut)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bills = db.query(Bill).filter(Bill.user_id == current_user.id).all()

    total_spend  = sum(b.amount_due for b in bills if b.amount_due) or 0.0
    total_kwh    = sum(b.usage_kwh  for b in bills if b.usage_kwh)  or 0
    total_carbon = sum(b.carbon_kg  for b in bills if b.carbon_kg)  or 0.0

    providers: Dict[str, int] = {}
    for b in bills:
        p = b.provider or "Unknown"
        providers[p] = providers.get(p, 0) + 1

    n = len(bills)
    return StatsOut(
        total_bills=n,
        total_spend=round(total_spend, 2),
        avg_monthly_kwh=round(total_kwh / n, 1) if n else 0.0,
        avg_monthly_cost=round(total_spend / n, 2) if n else 0.0,
        total_carbon_kg=round(total_carbon, 1),
        providers=providers,
    )


_ALLOWED_TYPES = {"image/jpeg", "image/png", "application/pdf"}
_MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


@app.post("/upload-bill", response_model=UploadResponse)
async def upload_bill(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if file.content_type and file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Upload a PDF, JPG, or PNG.",
        )

    filename = file.filename or "uploaded_bill"
    file_path = os.path.join(UPLOAD_DIR, filename)

    raw = await file.read()
    if len(raw) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(raw) // (1024*1024)} MB). Maximum allowed is 20 MB.",
        )

    with open(file_path, "wb") as buf:
        buf.write(raw)

    try:
        try:
            raw_text = extract_text(file_path)
        except (RuntimeError, ValueError) as ocr_err:
            raise HTTPException(status_code=422, detail=str(ocr_err))

        parsed: Dict[str, Any] = parse_bill(raw_text)

        bill = Bill(
            user_id=current_user.id,
            filename=filename,
            provider=parsed.get("provider", "Unknown"),
            account_number=parsed.get("account_number"),
            bill_date=parsed.get("bill_date"),
            due_date=parsed.get("due_date"),
            amount_due=parsed.get("amount_due"),
            usage_kwh=parsed.get("usage_kwh"),
            standing_charge=parsed.get("standing_charge"),
            unit_rate=parsed.get("unit_rate"),
            tariff_name=parsed.get("tariff_name"),
            meter_serial=parsed.get("meter_serial"),
            carbon_kg=parsed.get("carbon_kg"),
            raw_text=raw_text,
        )
        db.add(bill)
        db.commit()
        db.refresh(bill)

        # Spike alert: compare with previous bill's usage
        if current_user.email_alerts and bill.usage_kwh:
            prev_bills = (
                db.query(Bill)
                .filter(Bill.user_id == current_user.id, Bill.id != bill.id, Bill.usage_kwh.isnot(None))
                .order_by(Bill.id.desc())
                .limit(1)
                .all()
            )
            if prev_bills:
                prev_kwh = prev_bills[0].usage_kwh
                if prev_kwh and (bill.usage_kwh - prev_kwh) / prev_kwh > 0.15:
                    send_spike_alert(
                        to_email=current_user.email,
                        name=current_user.name or current_user.email,
                        current_kwh=bill.usage_kwh,
                        prev_kwh=prev_kwh,
                        bill_date=bill.bill_date or "",
                    )

        return UploadResponse(
            id=bill.id,
            filename=bill.filename,
            provider=bill.provider,
            account_number=bill.account_number,
            bill_date=bill.bill_date,
            due_date=bill.due_date,
            amount_due=bill.amount_due,
            usage_kwh=bill.usage_kwh,
            standing_charge=bill.standing_charge,
            unit_rate=bill.unit_rate,
            tariff_name=bill.tariff_name,
            meter_serial=bill.meter_serial,
            carbon_kg=bill.carbon_kg,
            extracted_text=raw_text[:500],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


class ManualBillIn(BaseModel):
    provider: str = "Unknown"
    account_number: str | None = None
    bill_date: str | None = None
    due_date: str | None = None
    amount_due: float | None = None
    usage_kwh: int | None = None
    standing_charge: float | None = None
    unit_rate: float | None = None
    tariff_name: str | None = None
    meter_serial: str | None = None


_CARBON_FACTOR = 0.197


@app.post("/bills/manual", response_model=BillOut)
def create_manual_bill(
    data: ManualBillIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    carbon = round(data.usage_kwh * _CARBON_FACTOR, 2) if data.usage_kwh else None
    bill = Bill(
        user_id=current_user.id,
        filename="manual_entry",
        provider=data.provider,
        account_number=data.account_number,
        bill_date=data.bill_date,
        due_date=data.due_date,
        amount_due=data.amount_due,
        usage_kwh=data.usage_kwh,
        standing_charge=data.standing_charge,
        unit_rate=data.unit_rate,
        tariff_name=data.tariff_name,
        meter_serial=data.meter_serial,
        carbon_kg=carbon,
        raw_text="",
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill


@app.get("/bills", response_model=List[BillOut])
def list_bills(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Bill)
        .filter(Bill.user_id == current_user.id)
        .order_by(Bill.id.desc())
        .all()
    )


@app.get("/bills/{bill_id}", response_model=BillOut)
def get_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bill = db.query(Bill).filter(Bill.id == bill_id, Bill.user_id == current_user.id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill


@app.get("/bills/{bill_id}/raw-text")
def get_bill_raw_text(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bill = db.query(Bill).filter(Bill.id == bill_id, Bill.user_id == current_user.id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return {"id": bill_id, "raw_text": bill.raw_text or ""}


class BillPatch(BaseModel):
    provider: str | None = None
    account_number: str | None = None
    bill_date: str | None = None
    due_date: str | None = None
    amount_due: float | None = None
    usage_kwh: int | None = None
    standing_charge: float | None = None
    unit_rate: float | None = None
    tariff_name: str | None = None
    meter_serial: str | None = None


@app.patch("/bills/{bill_id}", response_model=BillOut)
def update_bill(
    bill_id: int,
    data: BillPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bill = db.query(Bill).filter(Bill.id == bill_id, Bill.user_id == current_user.id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(bill, field, value)
    if bill.usage_kwh:
        bill.carbon_kg = round(bill.usage_kwh * _CARBON_FACTOR, 2)
    db.commit()
    db.refresh(bill)
    return bill


@app.delete("/bills/{bill_id}")
def delete_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bill = db.query(Bill).filter(Bill.id == bill_id, Bill.user_id == current_user.id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    db.delete(bill)
    db.commit()
    return {"deleted": bill_id}


# ─── BUDGET & ALERTS ENDPOINTS ────────────────────────────────────────────────

class BudgetIn(BaseModel):
    budget_monthly_gbp: float | None = None
    budget_monthly_kwh: int | None = None
    email_alerts: bool | None = None


class BudgetOut(BaseModel):
    budget_monthly_gbp: float | None
    budget_monthly_kwh: int | None
    email_alerts: bool


@app.put("/budget", response_model=BudgetOut)
def set_budget(
    data: BudgetIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if data.budget_monthly_gbp is not None:
        user.budget_monthly_gbp = data.budget_monthly_gbp
    if data.budget_monthly_kwh is not None:
        user.budget_monthly_kwh = data.budget_monthly_kwh
    if data.email_alerts is not None:
        user.email_alerts = data.email_alerts
    db.commit()
    db.refresh(user)
    return BudgetOut(
        budget_monthly_gbp=user.budget_monthly_gbp,
        budget_monthly_kwh=user.budget_monthly_kwh,
        email_alerts=bool(user.email_alerts),
    )


@app.get("/budget", response_model=BudgetOut)
def get_budget(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    return BudgetOut(
        budget_monthly_gbp=user.budget_monthly_gbp,
        budget_monthly_kwh=user.budget_monthly_kwh,
        email_alerts=bool(user.email_alerts),
    )


@app.get("/budget/status")
def budget_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns latest bill vs budget limits — used by the dashboard warning banner."""
    user = db.query(User).filter(User.id == current_user.id).first()
    bills = db.query(Bill).filter(Bill.user_id == current_user.id).order_by(Bill.id.desc()).all()

    latest_cost = next((b.amount_due for b in bills if b.amount_due), None)
    latest_kwh  = next((b.usage_kwh  for b in bills if b.usage_kwh),  None)

    gbp_limit = user.budget_monthly_gbp
    kwh_limit = user.budget_monthly_kwh

    def _pct(val, limit):
        return round(val / limit * 100, 1) if (val and limit and limit > 0) else None

    return {
        "budget_monthly_gbp": gbp_limit,
        "budget_monthly_kwh": kwh_limit,
        "latest_cost":        latest_cost,
        "latest_kwh":         latest_kwh,
        "cost_pct":           _pct(latest_cost, gbp_limit),
        "kwh_pct":            _pct(latest_kwh,  kwh_limit),
        "cost_status":        ("exceeded" if (latest_cost and gbp_limit and latest_cost > gbp_limit)
                               else "warning" if (_pct(latest_cost, gbp_limit) or 0) >= 80
                               else "ok"),
        "kwh_status":         ("exceeded" if (latest_kwh and kwh_limit and latest_kwh > kwh_limit)
                               else "warning" if (_pct(latest_kwh, kwh_limit) or 0) >= 80
                               else "ok"),
    }


@app.post("/alerts/weekly-summary")
def trigger_weekly_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user.email_alerts:
        raise HTTPException(status_code=400, detail="Email alerts are disabled. Enable them in Settings first.")
    bills = db.query(Bill).filter(Bill.user_id == current_user.id).order_by(Bill.id.desc()).all()
    if not bills:
        raise HTTPException(status_code=404, detail="No bills to summarise.")
    ok = send_weekly_summary(to_email=user.email, name=user.name or user.email, bills=bills)
    if not ok:
        raise HTTPException(status_code=503, detail="Failed to send email. Check SMTP settings in .env.")
    return {"sent": True, "to": user.email}


@app.post("/alerts/check-due-dates")
def check_due_dates(
    days_ahead: int = 3,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check bills with due dates within `days_ahead` days and send reminder emails."""
    from datetime import date, timedelta
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user.email_alerts:
        raise HTTPException(status_code=400, detail="Email alerts are disabled.")

    bills = db.query(Bill).filter(Bill.user_id == current_user.id, Bill.due_date.isnot(None)).all()
    today = date.today()
    sent = []

    for b in bills:
        if not b.due_date or not b.amount_due:
            continue
        from backend.ml import _parse_date
        dt = _parse_date(b.due_date)
        if not dt:
            continue
        due = dt.date()
        days_left = (due - today).days
        if 0 <= days_left <= days_ahead:
            ok = send_due_date_reminder(
                to_email=user.email,
                name=user.name or user.email,
                bill_id=b.id,
                provider=b.provider or "Unknown",
                due_date=b.due_date,
                amount_due=b.amount_due,
                days_left=days_left,
            )
            if ok:
                sent.append({"bill_id": b.id, "due_date": b.due_date, "days_left": days_left})

    return {"checked": len(bills), "reminders_sent": len(sent), "details": sent}


@app.get("/alerts/upcoming-dues")
def upcoming_dues(
    days_ahead: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return bills with due dates in the next N days (for dashboard display)."""
    from datetime import date
    bills = db.query(Bill).filter(Bill.user_id == current_user.id, Bill.due_date.isnot(None)).all()
    today = date.today()
    upcoming = []
    for b in bills:
        if not b.due_date:
            continue
        from backend.ml import _parse_date
        dt = _parse_date(b.due_date)
        if not dt:
            continue
        days_left = (dt.date() - today).days
        if 0 <= days_left <= days_ahead:
            upcoming.append({
                "bill_id": b.id, "provider": b.provider,
                "due_date": b.due_date, "amount_due": b.amount_due,
                "days_left": days_left,
            })
    upcoming.sort(key=lambda x: x["days_left"])
    return upcoming


class GoalIn(BaseModel):
    goal_reduction_pct: float
    goal_baseline_kwh: float | None = None


@app.put("/goal")
def set_goal(
    data: GoalIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    user.goal_reduction_pct = data.goal_reduction_pct

    if data.goal_baseline_kwh is not None:
        user.goal_baseline_kwh = data.goal_baseline_kwh
    elif user.goal_baseline_kwh is None:
        # Auto-set baseline from current average kWh
        bills = db.query(Bill).filter(Bill.user_id == current_user.id, Bill.usage_kwh.isnot(None)).all()
        if bills:
            user.goal_baseline_kwh = sum(b.usage_kwh for b in bills) / len(bills)

    db.commit()
    db.refresh(user)
    return {"goal_reduction_pct": user.goal_reduction_pct, "goal_baseline_kwh": user.goal_baseline_kwh}


@app.get("/goal")
def get_goal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    bills = db.query(Bill).filter(Bill.user_id == current_user.id, Bill.usage_kwh.isnot(None)).order_by(Bill.id.desc()).all()

    baseline = user.goal_baseline_kwh
    target_pct = user.goal_reduction_pct
    current_avg = sum(b.usage_kwh for b in bills[:3]) / min(len(bills), 3) if bills else None

    target_kwh = round(baseline * (1 - target_pct / 100), 1) if baseline and target_pct else None
    progress_pct = None
    if baseline and current_avg and target_kwh:
        reduction_achieved = baseline - current_avg
        reduction_needed   = baseline - target_kwh
        progress_pct = round(min(reduction_achieved / reduction_needed * 100, 100), 1) if reduction_needed else 100.0

    return {
        "goal_reduction_pct": target_pct,
        "goal_baseline_kwh":  baseline,
        "target_kwh":         target_kwh,
        "current_avg_kwh":    round(current_avg, 1) if current_avg else None,
        "progress_pct":       progress_pct,
        "on_track":           (current_avg <= target_kwh) if (current_avg and target_kwh) else None,
    }


# ─── ML ENDPOINTS ──────────────────────────────────────────────────────────────

@app.get("/ml/predictions")
def ml_predictions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bills = db.query(Bill).filter(Bill.user_id == current_user.id).order_by(Bill.id).all()
    return predict_next_month(bills)


@app.get("/ml/anomalies")
def ml_anomalies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bills = db.query(Bill).filter(Bill.user_id == current_user.id).order_by(Bill.id).all()
    return detect_anomalies(bills)


@app.get("/ml/classify")
def ml_classify(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bills = db.query(Bill).filter(Bill.user_id == current_user.id).order_by(Bill.id).all()
    return classify_usage(bills)


@app.get("/ml/recommendations")
def ml_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bills = db.query(Bill).filter(Bill.user_id == current_user.id).order_by(Bill.id).all()
    return generate_recommendations(bills)


@app.get("/ml/clusters")
def ml_clusters(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bills = db.query(Bill).filter(Bill.user_id == current_user.id).order_by(Bill.id).all()
    return cluster_usage(bills)


@app.get("/ml/changepoints")
def ml_changepoints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bills = db.query(Bill).filter(Bill.user_id == current_user.id).order_by(Bill.id).all()
    return detect_changepoints(bills)


@app.get("/ml/cost-prediction")
def ml_cost_prediction(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bills = db.query(Bill).filter(Bill.user_id == current_user.id).order_by(Bill.id).all()
    return predict_cost_gbr(bills)


# ─── REPORT ENDPOINTS ──────────────────────────────────────────────────────────

@app.get("/report/pdf")
def download_pdf_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    bills = db.query(Bill).filter(Bill.user_id == current_user.id).order_by(Bill.id).all()
    if not bills:
        raise HTTPException(status_code=404, detail="No bills found. Upload at least one bill to generate a report.")

    total_spend  = sum(b.amount_due for b in bills if b.amount_due) or 0.0
    total_kwh    = sum(b.usage_kwh  for b in bills if b.usage_kwh)  or 0
    total_carbon = sum(b.carbon_kg  for b in bills if b.carbon_kg)  or 0.0
    n = len(bills)
    stats = {
        "total_bills":     n,
        "total_spend":     round(total_spend, 2),
        "avg_monthly_kwh": round(total_kwh / n, 1) if n else 0.0,
        "total_carbon_kg": round(total_carbon, 1),
    }

    pdf_bytes = generate_pdf_report(
        user_email=current_user.email,
        user_name=current_user.name or "",
        bills=bills,
        stats=stats,
    )
    from datetime import datetime
    filename = f"energy_report_{datetime.now().strftime('%Y%m%d')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── EXPORT ENDPOINT ───────────────────────────────────────────────────────────

@app.get("/bills/export/csv")
def export_bills_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import csv, io
    bills = db.query(Bill).filter(Bill.user_id == current_user.id).order_by(Bill.id).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "ID", "Provider", "Bill Date", "Due Date",
        "Amount (£)", "Usage (kWh)", "Standing Charge (p/day)", "Unit Rate (p/kWh)",
        "CO₂ (kg)", "Tariff", "Account Number", "Meter Serial", "Uploaded At",
    ])
    for b in bills:
        writer.writerow([
            b.id, b.provider, b.bill_date, b.due_date,
            b.amount_due, b.usage_kwh, b.standing_charge, b.unit_rate,
            b.carbon_kg, b.tariff_name, b.account_number, b.meter_serial,
            b.uploaded_at.isoformat() if b.uploaded_at else "",
        ])
    from datetime import datetime
    filename = f"energy_bills_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ─── PROFILE ENDPOINTS ─────────────────────────────────────────────────────────

class NameIn(BaseModel):
    name: str


@app.put("/auth/me/name")
def update_display_name(
    data: NameIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == current_user.id).first()
    user.name = data.name.strip()
    db.commit()
    return {"name": user.name}


@app.delete("/auth/me")
def delete_my_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Bill).filter(Bill.user_id == current_user.id).delete()
    db.query(User).filter(User.id == current_user.id).delete()
    db.commit()
    return {"deleted": True}


# ─── ADMIN ENDPOINTS ───────────────────────────────────────────────────────────

@app.get("/admin/stats")
def admin_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    users = db.query(User).all()
    bills = db.query(Bill).all()
    total_spend  = sum(b.amount_due for b in bills if b.amount_due) or 0.0
    total_carbon = sum(b.carbon_kg  for b in bills if b.carbon_kg)  or 0.0
    return {
        "total_users": len(users),
        "total_bills": len(bills),
        "total_spend": round(total_spend, 2),
        "total_carbon_kg": round(total_carbon, 1),
    }


@app.get("/admin/users")
def admin_list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    users = db.query(User).order_by(User.id).all()
    result = []
    for u in users:
        bill_count = db.query(Bill).filter(Bill.user_id == u.id).count()
        result.append({
            "id": u.id,
            "email": u.email,
            "name": u.name,
            "is_admin": u.is_admin,
            "bill_count": bill_count,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })
    return result


@app.delete("/admin/users/{user_id}")
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),
):
    if user_id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.query(Bill).filter(Bill.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"deleted": user_id}


@app.get("/admin/bills")
def admin_list_bills(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    bills = db.query(Bill).order_by(Bill.id.desc()).all()
    result = []
    for b in bills:
        owner = db.query(User).filter(User.id == b.user_id).first()
        result.append({
            "id": b.id,
            "filename": b.filename,
            "provider": b.provider,
            "amount_due": b.amount_due,
            "usage_kwh": b.usage_kwh,
            "carbon_kg": b.carbon_kg,
            "bill_date": b.bill_date,
            "user_email": owner.email if owner else "Unknown",
            "user_id": b.user_id,
        })
    return result


@app.delete("/admin/bills/{bill_id}")
def admin_delete_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    bill = db.query(Bill).filter(Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    db.delete(bill)
    db.commit()
    return {"deleted": bill_id}
