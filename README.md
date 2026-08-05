# Smart Energy Auditor

An AI-powered energy bill analyser that extracts data from utility bills using OCR, forecasts future usage with machine learning, and provides personalised insights to help users reduce energy costs and carbon footprint.

**Live Demo:** [smart-energy-auditor.vercel.app](https://smart-energy-auditor.vercel.app) | **API:** [smart-energy-auditor.onrender.com](https://smart-energy-auditor.onrender.com)

---

## Features

- **Bill Upload & OCR Extraction** — Upload electricity/gas bills as PDF or image (JPG/PNG). Extracts bill date, due date, amount, usage (kWh), unit rate and tariff using Tesseract OCR and pdftotext
- **ML-Powered Forecasting** — Predicts next month's usage and cost using Prophet and Linear Regression
- **Anomaly Detection** — Identifies unusual consumption spikes using Isolation Forest
- **Usage Clustering** — Groups consumption patterns using KMeans clustering
- **Changepoint Detection** — Detects permanent usage shifts using PELT (ruptures)
- **CO2 Tracking** — Calculates carbon emissions per bill and tracks over time (0.197 kg/kWh)
- **UK Benchmarking** — Compares your usage against UK average (258 kWh/month, £130/month)
- **Savings Calculator** — Estimates potential annual savings based on usage patterns
- **Interactive Charts** — Visualises usage, cost and carbon trends using Plotly
- **Bill History** — Stores all uploaded bills in PostgreSQL with full history view
- **Multi-Provider Support** — British Gas, Octopus Energy, E.ON, OVO, EDF, Scottish Power and more

---

## Tech Stack

### Frontend
- React 19 + Vite
- Plotly.js (interactive charts)
- Deployed on **Vercel**

### Backend
- Python + FastAPI
- Tesseract OCR (pytesseract) + OpenCV
- pdftotext (poppler-utils) for digital PDFs
- Deployed on **Render** (Docker)

### Database
- PostgreSQL (Neon serverless)

### Machine Learning

| Model | Library | Purpose |
|-------|---------|---------|
| Prophet | `prophet` | Time series forecasting (≥4 bills) |
| Linear Regression | `scikit-learn` | Usage trend prediction (<4 bills) |
| Isolation Forest | `scikit-learn` | Anomaly detection (≥5 bills) |
| KMeans | `scikit-learn` | Consumption clustering |
| Gradient Boosting | `scikit-learn` | Cost prediction |
| PELT | `ruptures` | Changepoint detection |

---

## Architecture

```
Frontend (React/Vercel)
        ↓
Backend API (FastAPI/Render/Docker)
        ↓
   ┌────┴────┐
  OCR      ML Models
(Tesseract) (Prophet, sklearn)
        ↓
PostgreSQL (Neon)
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Tesseract OCR installed
- PostgreSQL database (or Neon account)

### Backend Setup

```bash
git clone https://github.com/Samishemanto/smart-energy-auditor.git
cd smart-energy-auditor/backend

pip install -r requirements.txt

# Create .env file
DATABASE_URL=your_postgresql_connection_string
TESSERACT_CMD=path/to/tesseract

uvicorn app:app --reload
```

### Frontend Setup

```bash
cd frontend-react
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (Neon) |
| `TESSERACT_CMD` | Path to Tesseract executable |
| `POPPLER_PATH` | Path to poppler binaries (optional) |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload and parse a bill |
| GET | `/bills` | Get all uploaded bills |
| GET | `/bills/{id}` | Get a specific bill |
| DELETE | `/bills/{id}` | Delete a bill |
| GET | `/ml/predict` | Get ML predictions and forecasts |
| GET | `/ml/anomalies` | Get anomaly detection results |
| GET | `/ml/clusters` | Get KMeans clustering results |
| GET | `/ml/changepoints` | Get changepoint detection results |
| GET | `/ml/recommendations` | Get personalised energy tips |

Full interactive docs at `/docs` (Swagger UI)

---

## Project Structure

```
smart-energy-auditor/
├── backend/
│   ├── app.py          # FastAPI routes
│   ├── bill_parser.py  # Bill text parsing & regex
│   ├── ocr.py          # OCR extraction (Tesseract/pdftotext)
│   ├── ml.py           # ML models & predictions
│   └── Dockerfile
├── frontend-react/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Insights.jsx
│   │   │   └── BillHistory.jsx
│   │   └── components/
└── README.md
```

---

## Author

**Samiur Rahman**
- GitHub: [@Samishemanto](https://github.com/Samishemanto)
- LinkedIn: [samiur-rahman-827210331](https://www.linkedin.com/in/samiur-rahman-827210331/)

---

## License

MIT
