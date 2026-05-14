# ⚡ Smart Energy Auditor

An AI-powered SaaS web app for analysing UK electricity and gas bills. Upload a PDF or photo of your bill — OCR extracts the data, ML models forecast your next bill, detect anomalies, cluster your usage patterns, and generate personalised recommendations.

![Python](https://img.shields.io/badge/Python-3.12-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-0.3.0-009688) ![Streamlit](https://img.shields.io/badge/Streamlit-frontend-FF4B4B) ![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

| Feature | Details |
|---|---|
| **OCR bill scanning** | Upload PDF, JPG, or PNG — Tesseract + OpenCV extracts text |
| **Manual entry** | Enter bill data by hand when no scan is available |
| **7 provider parsers** | British Gas, Scottish Power, Octopus Energy, E.ON, OVO Energy, EDF Energy, nPower |
| **Analytics dashboard** | KPI cards, time-series usage/cost charts, provider breakdown donut |
| **Forecasting** | Prophet (seasonal) with linear regression fallback |
| **Anomaly detection** | IsolationForest (5+ bills) or Z-score |
| **Usage clustering** | KMeans groups bills into Low / Medium / High patterns |
| **Changepoint detection** | Ruptures PELT algorithm detects permanent usage shifts |
| **Recommendations** | Personalised tips based on your unit rate, trend, and usage band |
| **Carbon tracking** | CO₂ footprint per bill (UK National Grid 0.197 kg/kWh) |
| **CSV export** | Download all bill data from History and Insights pages |
| **Google OAuth + JWT** | Secure login, per-user bill isolation |
| **Admin panel** | System-wide stats, user management, bill oversight |

---

## Tech Stack

```
Backend   FastAPI · SQLAlchemy · SQLite · Python 3.12
Frontend  Streamlit · Plotly · streamlit-option-menu
OCR       Tesseract · pdf2image · OpenCV · Pillow
ML        Prophet · scikit-learn · ruptures · NumPy
Auth      Google OAuth 2.0 · python-jose (JWT HS256)
```

---

## Quick Start

### Prerequisites

- Python 3.12+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) — Windows installer
- [Poppler](https://github.com/oschwartz10612/poppler-windows/releases/) — for PDF support
- A Google OAuth 2.0 client (free, takes ~5 min to set up)

### 1. Clone and install

```bash
git clone https://github.com/yourusername/smart-energy-auditor.git
cd smart-energy-auditor
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

### 2. Configure environment

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # Mac/Linux
```

Edit `.env`:

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
JWT_SECRET=run: python -c "import secrets; print(secrets.token_hex(32))"
STREAMLIT_URL=http://localhost:8501
ADMIN_EMAIL=your-email@gmail.com

# Windows paths (leave blank if on PATH)
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
POPPLER_PATH=C:\path\to\poppler\Library\bin
```

### 3. Set up Google OAuth

1. Go to [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials)
2. Create a new **OAuth 2.0 Client ID** (Web application)
3. Add authorised redirect URI: `http://127.0.0.1:8000/auth/callback`
4. Copy the Client ID and Secret into `.env`

### 4. Run

```bash
# Terminal 1 — Backend API
uvicorn backend.app:app --reload --port 8000

# Terminal 2 — Frontend
streamlit run frontend/ui.py
```

Open [http://localhost:8501](http://localhost:8501) and sign in with Google.

---

## Docker (one command)

```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:8501 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |

---

## Project Structure

```
smart-energy-auditor/
├── backend/
│   ├── app.py          # FastAPI routes + validation
│   ├── auth.py         # Google OAuth + JWT
│   ├── bill_parser.py  # Provider-specific regex parsers (7 providers)
│   ├── db.py           # SQLAlchemy engine + session
│   ├── ml.py           # Prophet, KMeans, IsolationForest, ruptures PELT
│   └── ocr.py          # Tesseract + pdf2image pipeline
├── database/
│   └── models.py       # SQLAlchemy models (User, Bill)
├── frontend/
│   └── ui.py           # Streamlit app — all pages + dark theme
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/auth/google` | Get Google OAuth URL |
| GET | `/auth/callback` | OAuth callback → JWT redirect |
| GET | `/auth/me` | Current user info |
| POST | `/upload-bill` | Upload + OCR + parse a bill (max 20 MB) |
| POST | `/bills/manual` | Create a bill manually |
| GET | `/bills` | List user's bills |
| DELETE | `/bills/{id}` | Delete a bill |
| GET | `/stats` | User dashboard stats |
| GET | `/ml/predictions` | Prophet/linear forecast |
| GET | `/ml/anomalies` | Anomaly detection |
| GET | `/ml/classify` | Usage band classification |
| GET | `/ml/clusters` | KMeans usage clustering |
| GET | `/ml/changepoints` | Changepoint detection |
| GET | `/ml/recommendations` | Personalised tips |
| GET | `/admin/stats` | System-wide stats (admin only) |
| GET | `/admin/users` | All users (admin only) |
| DELETE | `/admin/users/{id}` | Delete user + bills (admin only) |

Full interactive docs at `http://localhost:8000/docs`

---

## ML Models

| Model | Library | Trigger |
|---|---|---|
| Prophet (seasonal forecasting) | `prophet` | ≥4 bills with dates |
| Linear Regression (forecast fallback) | `scikit-learn` | <4 bills |
| IsolationForest (anomaly detection) | `scikit-learn` | ≥5 bills |
| Z-score (anomaly fallback) | `numpy` | 3–4 bills |
| KMeans (usage clustering) | `scikit-learn` | ≥3 bills with usage + cost |
| PELT (changepoint detection) | `ruptures` | ≥4 bills with dates |
| Sliding-window mean shift (fallback) | `numpy` | ruptures not installed |

---

## Supported Providers

British Gas · Scottish Power · Octopus Energy · E.ON · OVO Energy · EDF Energy · nPower · Shell Energy · Bulb Energy · So Energy · Generic fallback for any other UK provider

---

## License

MIT
