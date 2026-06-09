import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest, GradientBoostingRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from typing import List, Dict, Any, Optional
from datetime import datetime

CARBON_FACTOR = 0.197  # kg CO₂ per kWh, UK 2024
UK_AVG_UNIT_RATE = 24.0  # pence/kWh, Ofgem 2024
UK_AVG_ANNUAL_KWH = 3100  # Ofgem typical domestic


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _parse_date(date_str: str) -> Optional[datetime]:
    if not date_str:
        return None
    for fmt in ["%d %B %Y", "%d %b %Y", "%d/%m/%Y", "%Y-%m-%d"]:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None


# ─── PREDICTION (Prophet with linear regression fallback) ─────────────────────

def predict_next_month(bills) -> Dict[str, Any]:
    data = []
    for b in bills:
        if b.usage_kwh and b.bill_date:
            dt = _parse_date(b.bill_date)
            if dt:
                months = dt.year * 12 + dt.month
                data.append((months, b.usage_kwh, b.amount_due or 0.0, dt))

    if len(data) < 2:
        return {
            "status": "insufficient_data",
            "message": "Upload at least 2 bills with dates to enable predictions.",
            "min_bills_needed": 2,
        }

    data.sort(key=lambda x: x[0])

    # Try Prophet for seasonal forecasting when 4+ data points exist
    if len(data) >= 4:
        try:
            from prophet import Prophet  # type: ignore
            import pandas as pd

            df_p = pd.DataFrame({
                "ds": [d[3] for d in data],
                "y":  [float(d[1]) for d in data],
            })
            model = Prophet(yearly_seasonality=True, weekly_seasonality=False,
                            daily_seasonality=False, uncertainty_samples=0)
            model.fit(df_p)

            last_dt = data[-1][3]
            if last_dt.month == 12:
                next_dt = last_dt.replace(year=last_dt.year + 1, month=1)
            else:
                next_dt = last_dt.replace(month=last_dt.month + 1)

            future = model.make_future_dataframe(periods=1, freq="MS")
            forecast = model.predict(future)
            pred_kwh = max(0, round(float(forecast.iloc[-1]["yhat"])))

            # Cost: linear regression (no prophet model for cost)
            X = np.array([[d[0]] for d in data])
            y_cost = np.array([d[2] for d in data])
            pred_cost = max(0.0, round(float(
                LinearRegression().fit(X, y_cost).predict([[data[-1][0] + 1]])[0]
            ), 2))

            monthly_change = round(float(
                LinearRegression().fit(X, np.array([d[1] for d in data]))
                .coef_[0]
            ), 1)

            history = [
                {
                    "date": d[3].strftime("%b %Y"),
                    "kwh": d[1],
                    "cost": round(d[2], 2),
                    "carbon_kg": round(d[1] * CARBON_FACTOR, 2),
                }
                for d in data
            ]

            return {
                "status": "ok",
                "model": "prophet",
                "predicted_kwh": pred_kwh,
                "predicted_cost": pred_cost,
                "predicted_carbon_kg": round(pred_kwh * CARBON_FACTOR, 2),
                "model_r2": None,
                "data_points": len(data),
                "trend": "increasing" if monthly_change > 0 else "decreasing",
                "monthly_change_kwh": monthly_change,
                "next_period": next_dt.strftime("%B %Y"),
                "history": history,
            }
        except ImportError:
            pass  # prophet not installed — fall through to linear regression
        except Exception:
            pass  # any prophet error — fall through

    # Linear regression fallback
    X = np.array([[d[0]] for d in data])
    y_kwh = np.array([d[1] for d in data])
    y_cost = np.array([d[2] for d in data])

    model_kwh  = LinearRegression().fit(X, y_kwh)
    model_cost = LinearRegression().fit(X, y_cost)

    next_month = np.array([[data[-1][0] + 1]])
    pred_kwh  = max(0, round(float(model_kwh.predict(next_month)[0])))
    pred_cost = max(0.0, round(float(model_cost.predict(next_month)[0]), 2))
    r2 = round(float(model_kwh.score(X, y_kwh)), 3)
    monthly_change = round(float(model_kwh.coef_[0]), 1)

    last_dt = data[-1][3]
    if last_dt.month == 12:
        next_dt = last_dt.replace(year=last_dt.year + 1, month=1)
    else:
        next_dt = last_dt.replace(month=last_dt.month + 1)

    history = [
        {
            "date": d[3].strftime("%b %Y"),
            "kwh": d[1],
            "cost": round(d[2], 2),
            "carbon_kg": round(d[1] * CARBON_FACTOR, 2),
        }
        for d in data
    ]

    return {
        "status": "ok",
        "model": "linear_regression",
        "predicted_kwh": pred_kwh,
        "predicted_cost": pred_cost,
        "predicted_carbon_kg": round(pred_kwh * CARBON_FACTOR, 2),
        "model_r2": r2,
        "data_points": len(data),
        "trend": "increasing" if monthly_change > 0 else "decreasing",
        "monthly_change_kwh": monthly_change,
        "next_period": next_dt.strftime("%B %Y"),
        "history": history,
    }


# ─── GRADIENT BOOSTING COST PREDICTION ───────────────────────────────────────

def predict_cost_gbr(bills) -> Dict[str, Any]:
    """
    Gradient Boosting cost prediction using features:
    usage_kwh, unit_rate, standing_charge, month (seasonality), year.
    Requires at least 5 bills with usage_kwh and amount_due.
    """
    data = []
    for b in bills:
        if b.usage_kwh and b.amount_due and b.bill_date:
            dt = _parse_date(b.bill_date)
            if dt:
                data.append({
                    "usage_kwh":      b.usage_kwh,
                    "unit_rate":      b.unit_rate or UK_AVG_UNIT_RATE,
                    "standing_charge": b.standing_charge or 61.0,
                    "month":          dt.month,
                    "year":           dt.year,
                    "amount_due":     b.amount_due,
                })

    if len(data) < 5:
        return {
            "status": "insufficient_data",
            "message": "Upload at least 5 bills with usage and cost to enable GBR cost prediction.",
        }

    X = np.array([[d["usage_kwh"], d["unit_rate"], d["standing_charge"], d["month"], d["year"]] for d in data])
    y = np.array([d["amount_due"] for d in data])

    gbr = GradientBoostingRegressor(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=42)
    gbr.fit(X, y)

    # Predict next month using the last bill's features + 1 month
    last = data[-1]
    last_dt = _parse_date(bills[-1].bill_date)
    if last_dt.month == 12:
        next_month, next_year = 1, last_dt.year + 1
    else:
        next_month, next_year = last_dt.month + 1, last_dt.year

    # Use Prophet/linear predicted kWh if available — fallback to last usage
    next_usage = last["usage_kwh"]
    X_next = np.array([[next_usage, last["unit_rate"], last["standing_charge"], next_month, next_year]])
    pred_cost = max(0.0, round(float(gbr.predict(X_next)[0]), 2))

    # Feature importances
    feature_names = ["usage_kwh", "unit_rate", "standing_charge", "month", "year"]
    importances = {name: round(float(imp), 3)
                   for name, imp in zip(feature_names, gbr.feature_importances_)}

    # Cross-val R² (leave-one-out style capped at n=5)
    cv_folds = min(len(data), 5)
    cv_scores = cross_val_score(gbr, X, y, cv=cv_folds, scoring="r2")
    cv_r2 = round(float(np.mean(cv_scores)), 3)

    return {
        "status": "ok",
        "predicted_cost": pred_cost,
        "cv_r2": cv_r2,
        "feature_importances": importances,
        "data_points": len(data),
        "next_period": f"{datetime(next_year, next_month, 1).strftime('%B %Y')}",
    }


# ─── ANOMALY DETECTION ────────────────────────────────────────────────────────

def detect_anomalies(bills) -> List[Dict[str, Any]]:
    """Flag bills with unusual usage or cost. IsolationForest for 5+ bills, Z-score otherwise."""
    data = []
    for b in bills:
        if b.usage_kwh and b.amount_due:
            data.append({
                "id": b.id,
                "filename": b.filename,
                "usage_kwh": b.usage_kwh,
                "amount_due": b.amount_due,
                "bill_date": b.bill_date or "",
                "provider": b.provider,
            })

    if len(data) < 3:
        return []

    X = np.array([[d["usage_kwh"], d["amount_due"]] for d in data])

    if len(data) >= 5:
        clf = IsolationForest(contamination=0.2, random_state=42)
        labels = clf.fit_predict(X)
        anomaly_flags = labels == -1
    else:
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        anomaly_flags = np.any(np.abs(X_scaled) > 1.5, axis=1)

    mean_kwh = float(np.mean([d["usage_kwh"] for d in data]))
    result = []
    for d, is_anomaly in zip(data, anomaly_flags):
        if is_anomaly:
            pct_diff = round((d["usage_kwh"] - mean_kwh) / mean_kwh * 100, 1)
            result.append({
                **d,
                "pct_diff_from_mean": pct_diff,
                "reason": "unusually high usage" if pct_diff > 0 else "unusually low usage",
            })

    return result


# ─── USAGE CLASSIFICATION ─────────────────────────────────────────────────────

def classify_usage(bills) -> Dict[str, Any]:
    """Classify household as Low/Medium/High vs UK Ofgem annual bands."""
    kwh_values = [b.usage_kwh for b in bills if b.usage_kwh]
    if not kwh_values:
        return {
            "classification": "Unknown",
            "reason": "No usage data available. Upload bills with kWh readings.",
        }

    avg_monthly = sum(kwh_values) / len(kwh_values)
    annual_est = avg_monthly * 12

    if annual_est < 2000:
        classification, color = "Low", "#00C9B8"
        description = "Your household uses less energy than the UK average. Well done!"
    elif annual_est < 4000:
        classification, color = "Medium", "#F59E0B"
        description = "Your household is within the typical UK usage range."
    else:
        classification, color = "High", "#EF4444"
        description = "Your household uses more energy than the UK average. Consider an energy audit."

    return {
        "classification": classification,
        "color": color,
        "avg_monthly_kwh": round(avg_monthly),
        "estimated_annual_kwh": round(annual_est),
        "uk_average_annual_kwh": UK_AVG_ANNUAL_KWH,
        "description": description,
        "pct_vs_uk_avg": round((annual_est - UK_AVG_ANNUAL_KWH) / UK_AVG_ANNUAL_KWH * 100, 1),
    }


# ─── KMEANS USAGE CLUSTERING ──────────────────────────────────────────────────

def cluster_usage(bills) -> Dict[str, Any]:
    """
    Cluster bills into usage patterns using KMeans.
    Returns cluster labels, centroids, and a human-readable pattern name per bill.
    Requires at least 3 bills with both usage_kwh and amount_due.
    """
    data = []
    for b in bills:
        if b.usage_kwh and b.amount_due:
            data.append({
                "id": b.id,
                "bill_date": b.bill_date or "",
                "usage_kwh": b.usage_kwh,
                "amount_due": b.amount_due,
                "provider": b.provider,
            })

    if len(data) < 3:
        return {
            "status": "insufficient_data",
            "message": "Upload at least 3 bills with usage and cost data to enable clustering.",
        }

    X = np.array([[d["usage_kwh"], d["amount_due"]] for d in data])
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    n_clusters = min(3, len(data))
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)

    centroids_scaled = km.cluster_centers_
    centroids = scaler.inverse_transform(centroids_scaled)

    # Name clusters by kwh centroid rank: Low / Medium / High
    kwh_rank = np.argsort(centroids[:, 0])
    cluster_names = {int(kwh_rank[i]): name for i, name in
                     enumerate(["Low Usage", "Medium Usage", "High Usage"][:n_clusters])}
    cluster_colors = {int(kwh_rank[i]): color for i, color in
                      enumerate(["#00C9B8", "#F59E0B", "#EF4444"][:n_clusters])}

    clustered = []
    for d, label in zip(data, labels):
        clustered.append({
            **d,
            "cluster": int(label),
            "cluster_name": cluster_names[int(label)],
            "cluster_color": cluster_colors[int(label)],
        })

    summary = []
    for i in range(n_clusters):
        members = [d for d in clustered if d["cluster"] == i]
        summary.append({
            "cluster": i,
            "name": cluster_names[i],
            "color": cluster_colors[i],
            "count": len(members),
            "avg_kwh": round(float(np.mean([m["usage_kwh"] for m in members])), 1),
            "avg_cost": round(float(np.mean([m["amount_due"] for m in members])), 2),
        })

    return {
        "status": "ok",
        "n_clusters": n_clusters,
        "bills": clustered,
        "summary": summary,
    }


# ─── CHANGEPOINT DETECTION ────────────────────────────────────────────────────

def detect_changepoints(bills) -> Dict[str, Any]:
    """
    Detect permanent shifts in usage using a simple sliding-window mean comparison.
    Falls back gracefully when ruptures is not installed.
    Requires at least 4 bills with usage_kwh and bill_date.
    """
    data = []
    for b in sorted(bills, key=lambda x: (_parse_date(x.bill_date) or datetime.min)):
        if b.usage_kwh and b.bill_date:
            data.append({"id": b.id, "bill_date": b.bill_date, "usage_kwh": b.usage_kwh})

    if len(data) < 4:
        return {
            "status": "insufficient_data",
            "message": "Upload at least 4 bills with dates and usage to detect changepoints.",
        }

    signal = np.array([d["usage_kwh"] for d in data], dtype=float)
    changepoint_indices = []

    # Try ruptures library first
    try:
        import ruptures as rpt  # type: ignore
        algo = rpt.Pelt(model="rbf", min_size=2).fit(signal.reshape(-1, 1))
        result = algo.predict(pen=10)
        changepoint_indices = [i - 1 for i in result[:-1]]  # ruptures returns 1-indexed end of segment
    except ImportError:
        # Fallback: sliding window mean-shift detection
        for i in range(1, len(signal) - 1):
            before = np.mean(signal[:i])
            after  = np.mean(signal[i:])
            if before > 0 and abs(after - before) / before > 0.25:
                changepoint_indices.append(i)

    changepoints = []
    for idx in changepoint_indices:
        if idx < len(data):
            before_mean = float(np.mean(signal[:idx])) if idx > 0 else float(signal[0])
            after_mean  = float(np.mean(signal[idx:]))
            pct = round((after_mean - before_mean) / before_mean * 100, 1) if before_mean else 0
            changepoints.append({
                "bill_id": data[idx]["id"],
                "bill_date": data[idx]["bill_date"],
                "usage_kwh": data[idx]["usage_kwh"],
                "before_avg_kwh": round(before_mean, 1),
                "after_avg_kwh": round(after_mean, 1),
                "pct_change": pct,
                "direction": "increase" if pct > 0 else "decrease",
            })

    return {
        "status": "ok",
        "changepoints": changepoints,
        "total_bills_analysed": len(data),
    }


# ─── RECOMMENDATIONS ──────────────────────────────────────────────────────────

_UK_AVG_ANNUAL_SPEND = 1568  # £/year, Ofgem 2024
_UK_AVG_SC_PDAY      = 61.0  # pence/day standing charge, Ofgem 2024
_UK_AVG_CO2_ANNUAL   = 3100 * CARBON_FACTOR  # ~610 kg/year


def generate_recommendations(bills) -> List[Dict[str, Any]]:
    """Generate prioritised, personalised recommendations from bill history."""
    recs: List[Dict[str, Any]] = []

    # Sort bills by date for trend analysis
    dated: List[tuple] = []
    for b in bills:
        if b.bill_date:
            dt = _parse_date(b.bill_date)
            if dt:
                dated.append((dt, b))
    dated.sort(key=lambda x: x[0])
    sorted_bills = [b for _, b in dated]

    kwh_values     = [b.usage_kwh      for b in sorted_bills if b.usage_kwh]
    cost_values    = [b.amount_due     for b in sorted_bills if b.amount_due]
    unit_rates     = [b.unit_rate      for b in sorted_bills if b.unit_rate]
    carbon_values  = [b.carbon_kg      for b in sorted_bills if b.carbon_kg]
    s_charges      = [b.standing_charge for b in bills       if b.standing_charge]

    # ── 1. Month-over-month usage spike / drop ─────────────────────────────
    if len(kwh_values) >= 2:
        recent, prev = kwh_values[-1], kwh_values[-2]
        if prev > 0:
            pct = (recent - prev) / prev * 100
            if pct > 20:
                recs.append({
                    "priority": 1, "type": "warning",
                    "title": f"Usage spike: +{pct:.0f}%",
                    "detail": (f"Your latest bill shows {recent} kWh — up {pct:.0f}% from the previous "
                               f"({prev} kWh). Check for appliances on standby, heating thermostat changes, "
                               "or a draughty door or window."),
                })
            elif pct > 8:
                recs.append({
                    "priority": 2, "type": "warning",
                    "title": f"Usage crept up {pct:.0f}%",
                    "detail": (f"A moderate rise from {prev} kWh to {recent} kWh. Worth reviewing heating "
                               "schedules or checking for devices left on overnight."),
                })
            elif pct < -20:
                recs.append({
                    "priority": 1, "type": "success",
                    "title": f"Great saving: −{abs(pct):.0f}%",
                    "detail": (f"Usage dropped from {prev} kWh to {recent} kWh — excellent work! "
                               "Keep up those energy habits and consider locking in a cheaper tariff."),
                })
            elif pct < -8:
                recs.append({
                    "priority": 3, "type": "success",
                    "title": f"Usage down {abs(pct):.0f}% — nice",
                    "detail": f"Down from {prev} kWh to {recent} kWh. Small wins add up — you're on the right track.",
                })

    # ── 2. Multi-bill linear trend ─────────────────────────────────────────
    if len(kwh_values) >= 3:
        X = np.array(range(len(kwh_values)), dtype=float).reshape(-1, 1)
        slope = float(LinearRegression().fit(X, np.array(kwh_values)).coef_[0])
        if slope > 12:
            cost_impact = round(slope * (unit_rates[-1] if unit_rates else UK_AVG_UNIT_RATE) / 100 * 12, 0)
            recs.append({
                "priority": 1, "type": "warning",
                "title": "Consistently rising usage",
                "detail": (f"Usage has trended upward by ~{slope:.0f} kWh/bill across your last "
                           f"{len(kwh_values)} bills — that's ~£{cost_impact:.0f}/year extra at current rates. "
                           "A home energy audit or loft insulation could reverse this."),
            })
        elif slope < -12:
            recs.append({
                "priority": 3, "type": "success",
                "title": "Sustained usage reduction",
                "detail": (f"Usage is falling by ~{abs(slope):.0f} kWh/bill over your last "
                           f"{len(kwh_values)} bills — your efficiency improvements are working."),
            })

    # ── 3. Unit rate vs Ofgem average ─────────────────────────────────────
    if unit_rates:
        avg_rate = sum(unit_rates) / len(unit_rates)
        avg_kwh  = sum(kwh_values) / len(kwh_values) if kwh_values else 300
        if avg_rate > UK_AVG_UNIT_RATE + 5:
            saving = round((avg_rate - UK_AVG_UNIT_RATE) / 100 * avg_kwh * 12, 0)
            recs.append({
                "priority": 1, "type": "warning",
                "title": f"High unit rate: {avg_rate:.1f}p/kWh",
                "detail": (f"Your average unit rate is {avg_rate:.1f}p/kWh vs the UK average of "
                           f"~{UK_AVG_UNIT_RATE}p/kWh. Switching tariff could save ~£{saving:.0f}/year. "
                           "Compare on Ofgem's tariff checker or uSwitch."),
            })
        elif avg_rate > UK_AVG_UNIT_RATE + 2:
            recs.append({
                "priority": 3, "type": "info",
                "title": f"Tariff worth checking: {avg_rate:.1f}p/kWh",
                "detail": (f"Your unit rate is slightly above average. A quick tariff comparison "
                           "could shave £50–£100 off your annual bill."),
            })

    # ── 4. Standing charge vs average ─────────────────────────────────────
    if s_charges:
        avg_sc = sum(s_charges) / len(s_charges)
        if avg_sc > _UK_AVG_SC_PDAY + 10:
            extra = round((avg_sc - _UK_AVG_SC_PDAY) / 100 * 365, 0)
            recs.append({
                "priority": 2, "type": "warning",
                "title": f"High standing charge: {avg_sc:.1f}p/day",
                "detail": (f"Your standing charge ({avg_sc:.1f}p/day) is above the UK average "
                           f"(~{_UK_AVG_SC_PDAY}p/day) — costing ~£{extra:.0f}/year just to stay connected. "
                           "Some tariffs offer lower standing charges with higher unit rates that suit low-usage homes."),
            })

    # ── 5. Annual spend projection ─────────────────────────────────────────
    if cost_values and len(cost_values) >= 2:
        annual_est = (sum(cost_values) / len(cost_values)) * 12
        if annual_est > _UK_AVG_ANNUAL_SPEND * 1.25:
            over_pct = round((annual_est / _UK_AVG_ANNUAL_SPEND - 1) * 100)
            recs.append({
                "priority": 2, "type": "warning",
                "title": f"Annual spend ~£{annual_est:.0f} — {over_pct}% above average",
                "detail": (f"Projected annual energy spend of £{annual_est:.0f} is {over_pct}% above "
                           f"the UK average of ~£{_UK_AVG_ANNUAL_SPEND}. Tariff switching, loft insulation "
                           "or a heat pump could significantly reduce this."),
            })
        else:
            recs.append({
                "priority": 4, "type": "info",
                "title": f"Projected annual spend: ~£{annual_est:.0f}",
                "detail": (f"Based on your bills, your estimated annual spend is £{annual_est:.0f} — "
                           f"{'within the typical UK range' if annual_est <= _UK_AVG_ANNUAL_SPEND else 'slightly above average'}."),
            })

    # ── 6. High annual usage → smart meter suggestion ──────────────────────
    if kwh_values:
        avg_kwh    = sum(kwh_values) / len(kwh_values)
        annual_kwh = avg_kwh * 12
        rate       = unit_rates[-1] if unit_rates else UK_AVG_UNIT_RATE
        if annual_kwh > 4500:
            saving_lo = round(annual_kwh * rate / 100 * 0.03)
            saving_hi = round(annual_kwh * rate / 100 * 0.08)
            recs.append({
                "priority": 2, "type": "warning",
                "title": f"High annual usage: ~{annual_kwh:.0f} kWh",
                "detail": (f"Above the UK average of {UK_AVG_ANNUAL_KWH} kWh/year. A smart meter with "
                           f"a real-time display typically cuts usage 3–8% (£{saving_lo}–£{saving_hi}/year). "
                           "Loft insulation or cavity wall insulation can reduce this further."),
            })
        elif annual_kwh > 3800:
            recs.append({
                "priority": 4, "type": "info",
                "title": "Consider a smart meter",
                "detail": (f"At ~{annual_kwh:.0f} kWh/year, a smart meter could save 3–8% by helping "
                           "you spot high-consumption appliances in real time."),
            })

    # ── 7. CO₂ spike on latest bill ───────────────────────────────────────
    if len(carbon_values) >= 2:
        recent_co2, prev_co2 = carbon_values[-1], carbon_values[-2]
        if prev_co2 > 0 and (recent_co2 - prev_co2) / prev_co2 > 0.2:
            recs.append({
                "priority": 2, "type": "warning",
                "title": f"CO₂ up {((recent_co2 - prev_co2)/prev_co2*100):.0f}% this bill",
                "detail": (f"Carbon footprint rose from {prev_co2:.1f} kg to {recent_co2:.1f} kg. "
                           "Consider switching to a 100% renewable tariff — Octopus Energy, EDF Renewables, "
                           "or Bulb's successor offer verified green electricity."),
            })

    # ── 8. Annual carbon vs UK average ────────────────────────────────────
    if carbon_values:
        annual_co2 = (sum(carbon_values) / len(carbon_values)) * 12
        if annual_co2 > _UK_AVG_CO2_ANNUAL * 1.3:
            trees = round(annual_co2 / 21.7)
            over  = round((annual_co2 / _UK_AVG_CO2_ANNUAL - 1) * 100)
            recs.append({
                "priority": 3, "type": "info",
                "title": f"Carbon {over}% above UK average",
                "detail": (f"Estimated annual CO₂: {annual_co2:.0f} kg vs UK average of ~{_UK_AVG_CO2_ANNUAL:.0f} kg. "
                           f"Planting {trees} trees would offset this — or a green tariff eliminates it entirely."),
            })

    # ── 9. Seasonal awareness ─────────────────────────────────────────────
    if dated:
        last_month = dated[-1][0].month
        if last_month in (11, 12, 1, 2):
            recs.append({
                "priority": 4, "type": "info",
                "title": "Peak winter billing period",
                "detail": ("Heating accounts for ~60% of UK energy bills in winter. Dropping your thermostat "
                           "by 1°C saves ~£115/year. A timer programme so heating is off when you're out "
                           "saves even more."),
            })
        elif last_month in (6, 7, 8) and kwh_values:
            recs.append({
                "priority": 4, "type": "success",
                "title": "Summer billing — lowest usage season",
                "detail": ("Summer is the best time to lock in a fixed-rate tariff before winter prices rise. "
                           "Compare deals now to protect against Q4 price increases."),
            })

    # ── 10. Variable usage → time-of-use tariff ───────────────────────────
    if len(kwh_values) >= 3:
        arr = np.array(kwh_values, dtype=float)
        cv  = float(np.std(arr) / np.mean(arr)) if np.mean(arr) > 0 else 0
        if cv > 0.30:
            recs.append({
                "priority": 4, "type": "info",
                "title": "Highly variable usage — try a flexible tariff",
                "detail": (f"Your usage varies significantly (coefficient of variation: {cv:.0%}). "
                           "A time-of-use tariff like Octopus Agile lets you shift laundry, EV charging, "
                           "and dishwasher use to cheap overnight periods — potential 10–20% saving."),
            })

    # Sort by priority (1 = highest urgency), then strip internal field
    recs.sort(key=lambda r: r.get("priority", 5))
    for r in recs:
        r.pop("priority", None)

    if not recs:
        recs.append({
            "type": "info",
            "title": "Upload more bills to unlock insights",
            "detail": "Add at least 2–3 bills with usage data and dates to get personalised recommendations based on your real consumption patterns.",
        })

    return recs
