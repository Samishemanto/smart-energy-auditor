"""SMTP email alerts for Smart Energy Auditor.

Configure via .env:
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=your@gmail.com
    SMTP_PASS=your_app_password   # Gmail: Settings → Security → App Passwords
    SMTP_FROM=Smart Energy Auditor <your@gmail.com>
"""
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

def _smtp_config():
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    passwd = os.getenv("SMTP_PASS", "")
    sender = os.getenv("SMTP_FROM", user)
    return host, port, user, passwd, sender

_CSS = """
  body{margin:0;padding:0;background:#060B17;font-family:Helvetica,Arial,sans-serif;}
  .wrap{max-width:560px;margin:32px auto;background:#0C1525;border:1px solid #1A2840;
        border-radius:14px;overflow:hidden;}
  .head{background:linear-gradient(135deg,#00C9B8,#1D4ED8);padding:28px 32px;}
  .head h1{margin:0;color:#fff;font-size:1.3rem;font-weight:800;}
  .head p{margin:6px 0 0;color:rgba(255,255,255,0.75);font-size:0.85rem;}
  .body{padding:28px 32px;}
  .kpi{display:inline-block;background:#0A1018;border:1px solid #1A2840;border-radius:10px;
       padding:14px 22px;margin:0 8px 12px 0;}
  .kpi-val{font-size:1.5rem;font-weight:800;color:#F1F5F9;}
  .kpi-lab{font-size:0.72rem;color:#4B6280;text-transform:uppercase;letter-spacing:0.05em;}
  .tip{background:#0A1018;border-left:3px solid #00C9B8;border-radius:6px;
       padding:10px 14px;margin-bottom:8px;color:#94A3B8;font-size:0.83rem;line-height:1.5;}
  .btn{display:inline-block;background:linear-gradient(135deg,#00C9B8,#1D4ED8);
       color:#fff;font-weight:700;font-size:0.9rem;padding:12px 28px;border-radius:10px;
       text-decoration:none;margin-top:16px;}
  .foot{padding:16px 32px;border-top:1px solid #1A2840;font-size:0.72rem;color:#4B6280;text-align:center;}
"""


def _send(to: str, subject: str, html: str) -> bool:
    """Return True if sent, False if SMTP not configured or send failed."""
    host, port, user, passwd, sender = _smtp_config()
    if not (host and user and passwd):
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = sender
        msg["To"]      = to
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(host, port, timeout=10) as s:
            s.ehlo()
            s.starttls()
            s.login(user, passwd)
            s.sendmail(sender, to, msg.as_string())
        return True
    except Exception:
        return False


def send_spike_alert(to_email: str, name: str, current_kwh: int, prev_kwh: int, bill_date: str) -> bool:
    pct = round((current_kwh - prev_kwh) / prev_kwh * 100)
    subject = f"⚡ Energy spike alert — usage up {pct}% on your latest bill"
    html = f"""<!DOCTYPE html><html><head><style>{_CSS}</style></head><body>
<div class="wrap">
  <div class="head">
    <h1>⚡ Usage Spike Detected</h1>
    <p>Smart Energy Auditor · {datetime.now().strftime('%d %B %Y')}</p>
  </div>
  <div class="body">
    <p style="color:#CBD5E1;font-size:0.9rem;margin-top:0;">Hi {name},</p>
    <p style="color:#94A3B8;font-size:0.87rem;line-height:1.6;">
      Your latest bill ({bill_date or 'recent'}) shows a <strong style="color:#F59E0B;">{pct}% increase</strong>
      in energy usage compared to your previous bill.
    </p>
    <div>
      <div class="kpi">
        <div class="kpi-val">{current_kwh} kWh</div>
        <div class="kpi-lab">Latest bill</div>
      </div>
      <div class="kpi">
        <div class="kpi-val">{prev_kwh} kWh</div>
        <div class="kpi-lab">Previous bill</div>
      </div>
      <div class="kpi">
        <div class="kpi-val" style="color:#EF4444;">+{pct}%</div>
        <div class="kpi-lab">Change</div>
      </div>
    </div>
    <p style="color:#94A3B8;font-size:0.87rem;margin-top:16px;">Things to check:</p>
    <div class="tip">🔌 Appliances left on standby — TVs, gaming consoles, and chargers can add 10–15% to your bill.</div>
    <div class="tip">🌡️ Thermostat set too high — dropping 1°C saves ~£115/year.</div>
    <div class="tip">🚪 Draughts or poorly insulated windows can significantly increase heating load.</div>
  </div>
  <div class="foot">Smart Energy Auditor · Unsubscribe in Settings → Email Alerts</div>
</div></body></html>"""
    return _send(to_email, subject, html)


def send_weekly_summary(to_email: str, name: str, bills: list) -> bool:
    n           = len(bills)
    total_spend = sum(b.amount_due for b in bills if b.amount_due) or 0
    total_kwh   = sum(b.usage_kwh  for b in bills if b.usage_kwh)  or 0
    total_co2   = sum(b.carbon_kg  for b in bills if b.carbon_kg)  or 0
    avg_cost    = round(total_spend / n, 2) if n else 0
    kwh_values  = [b.usage_kwh for b in bills if b.usage_kwh]
    trend       = ""
    if len(kwh_values) >= 2:
        chg = (kwh_values[-1] - kwh_values[-2]) / kwh_values[-2] * 100
        trend = f'<div class="kpi"><div class="kpi-val" style="color:{"#EF4444" if chg > 0 else "#10B981"};">{chg:+.0f}%</div><div class="kpi-lab">Usage trend</div></div>'

    subject = f"⚡ Your energy summary — {n} bill{'s' if n != 1 else ''} analysed"
    html = f"""<!DOCTYPE html><html><head><style>{_CSS}</style></head><body>
<div class="wrap">
  <div class="head">
    <h1>⚡ Your Energy Summary</h1>
    <p>Smart Energy Auditor · {datetime.now().strftime('%d %B %Y')}</p>
  </div>
  <div class="body">
    <p style="color:#CBD5E1;font-size:0.9rem;margin-top:0;">Hi {name},</p>
    <p style="color:#94A3B8;font-size:0.87rem;line-height:1.6;">
      Here's a snapshot of your energy data across {n} bill{'s' if n != 1 else ''}.
    </p>
    <div>
      <div class="kpi"><div class="kpi-val">£{total_spend:,.2f}</div><div class="kpi-lab">Total spend</div></div>
      <div class="kpi"><div class="kpi-val">{total_kwh:,} kWh</div><div class="kpi-lab">Total usage</div></div>
      <div class="kpi"><div class="kpi-val">£{avg_cost}</div><div class="kpi-lab">Avg per bill</div></div>
      <div class="kpi"><div class="kpi-val">{total_co2:.0f} kg</div><div class="kpi-lab">CO₂ generated</div></div>
      {trend}
    </div>
    <div class="tip">💡 Drop your thermostat by 1°C — saves up to £115/year.</div>
    <div class="tip">🌙 Run washing machines off-peak (after 10pm) to cut costs.</div>
    <div class="tip">🔌 Switching off standby devices saves £55–£80/year.</div>
  </div>
  <div class="foot">Smart Energy Auditor · Unsubscribe in Settings → Email Alerts</div>
</div></body></html>"""
    return _send(to_email, subject, html)


def send_due_date_reminder(to_email: str, name: str, bill_id: int,
                           provider: str, due_date: str, amount_due: float,
                           days_left: int) -> bool:
    urgency_color = "#EF4444" if days_left <= 1 else "#F59E0B" if days_left <= 3 else "#1D4ED8"
    urgency_word  = "TODAY" if days_left == 0 else "TOMORROW" if days_left == 1 else f"in {days_left} days"
    subject = f"Energy bill due {urgency_word} — {provider} £{amount_due:.2f}"
    html = f"""<!DOCTYPE html><html><head><style>{_CSS}</style></head><body>
<div class="wrap">
  <div class="head">
    <h1>💳 Bill Payment Reminder</h1>
    <p>Smart Energy Auditor · {datetime.now().strftime('%d %B %Y')}</p>
  </div>
  <div class="body">
    <p style="color:#CBD5E1;font-size:0.9rem;margin-top:0;">Hi {name},</p>
    <p style="color:#94A3B8;font-size:0.87rem;line-height:1.6;">
      Your <b style="color:#F1F5F9;">{provider}</b> energy bill is due
      <b style="color:{urgency_color};">{urgency_word}</b>.
    </p>
    <div>
      <div class="kpi"><div class="kpi-val">£{amount_due:.2f}</div><div class="kpi-lab">Amount due</div></div>
      <div class="kpi"><div class="kpi-val" style="color:{urgency_color};">{urgency_word}</div><div class="kpi-lab">Payment due</div></div>
      <div class="kpi"><div class="kpi-val">{due_date}</div><div class="kpi-lab">Due date</div></div>
    </div>
    <div class="tip">💡 Set up a Direct Debit to avoid late payment charges and protect your credit score.</div>
  </div>
  <div class="foot">Smart Energy Auditor · Bill #{bill_id} · Unsubscribe in Alerts page</div>
</div></body></html>"""
    return _send(to_email, subject, html)
