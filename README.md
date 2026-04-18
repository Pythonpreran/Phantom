# 🛡️ PHANTOM
### AI-Driven Threat Detection & Simulation Engine

> Real-time cybersecurity defense powered by LightGBM + CDL behavioural intelligence.  
> Built for **Hack Malenadu '26 — Problem Statement 3**.

---

## What is PHANTOM?

PHANTOM is a full-stack cybersecurity platform that **detects, classifies, and responds to network attacks in real time** using a production-grade machine learning pipeline. It simulates a protected web application (XYZ Corp) where users can perform real attacks — SQL injection, XSS, DDoS, port scans, and brute force — and watch the AI defense system detect and block them live.

The system runs a **LightGBM model** (tuned with Optuna Bayesian search) trained on the UNSW-NB15 dataset, a **Cyber Defense Logic (CDL) engine** for behavioural threat intelligence, and a **SOC Kill Chain tracker** mapped to MITRE ATT&CK.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        PHANTOM Web App                       │
│                                                             │
│  React Frontend (Vite)          FastAPI Backend             │
│  ┌──────────────────┐           ┌─────────────────────┐    │
│  │  Landing Page    │           │  ML Engine           │    │
│  │  Login / Auth    │◄──────────│  LightGBM (Optuna)  │    │
│  │  Admin SOC Dash  │  REST +   │  CDL Engine          │    │
│  │  Company View    │  WebSocket│  SOC Kill Chain      │    │
│  │  User Dashboard  │           │  Honeypot            │    │
│  │  Validation Lab  │           │  SQLite DB           │    │
│  └──────────────────┘           └─────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18 + Vite, Vanilla CSS, Lucide Icons |
| **Backend** | FastAPI (Python 3.11+) |
| **ML Model** | LightGBM (Optuna Bayesian tuning), trained on UNSW-NB15 |
| **CDL Engine** | Custom behavioural threat intelligence (attacker memory, next-move prediction) |
| **Database** | SQLite via SQLAlchemy |
| **Real-time** | WebSocket broadcast to admin dashboard |
| **Alerts** | Twilio SMS + Voice call (optional, toggle in UI) |
| **Auth** | JWT (python-jose) |

---

## Features

### 🧠 ML Detection Pipeline
- **LightGBM model** (Optuna-tuned) trained on 2.5M+ UNSW-NB15 records
- 200+ engineered features: `packet_ratio`, `byte_per_packet`, `flow_duration_log`, `jitter_ratio`, etc.
- MinMaxScaler + feature selector → real-time `predict_proba()` per request
- Feature attribution shown live (SHAP-style importance bars)

### 🔗 CDL — Cyber Defense Logic Engine
- **Attacker Memory**: per-IP hit ratio, endpoint access patterns, activity timeline
- **Next-Move Predictor**: forecasts attacker's probable next action + ETA
- **Countermeasure Selector**: escalating responses — MONITOR → HONEYPOT → DELAY → DECEIVE

### ⛓️ SOC Kill Chain Tracker
- Tracks MITRE ATT&CK kill chain stage per attacker IP
- Stages: RECON → INITIAL ACCESS → EXECUTION → LATERAL MOVE → EXFILTRATION
- Per-attack MITRE ID + technique name shown in admin dashboard

### 🎯 Attack Simulation — User Dashboard
The "Normal User Actions" panel doubles as a live attack surface. Each form field is a real attack vector:

| Attack | Where | How |
|---|---|---|
| 🔨 **Brute Force** | Login form | Type wrong passwords 5× — ML risk score escalates per attempt |
| 💉 **SQL Injection** | Login username field | Paste `' OR 1=1 --` or `admin'; DROP TABLE users;--` |
| 🕷️ **XSS** | Contact form message | Paste `<script>alert('XSS')</script>` |
| 🌩️ **DDoS** | Fetch Data or Flood input | Click GET 5× in 10s (rate), or set packet count + Launch Flood |
| 🔍 **Port Scan** | Endpoint Probe field | Paste `/admin, /env, /config, /.git, /ssh` |

All 5 go through the **real LightGBM model** → CDL engine → auto-block + admin alert.

### 📡 Real-Time Admin SOC Dashboard
- Live WebSocket feed of all requests, ML predictions, confidence scores
- Alerts table (CRITICAL / HIGH / MEDIUM / LOW)
- Blocked IPs management with one-click unblock
- CDL intelligence context per event
- Twilio SMS/Voice toggle for critical alerts

### 🍯 Honeypot
- Fake endpoints that log attacker reconnaissance behaviour
- Decoy data served to high-risk IPs (CDL DECEIVE countermeasure)

### 🧪 Validation Lab
- Company dashboard feature to run structured attack validation tests
- Pass/fail scoring, accuracy, false-positive rate per attack category

---

## Default Accounts

| Role | Email | Password |
|---|---|---|
| Admin | `admin@phantom.io` | `admin123` |
| Company | `company@xyz.com` | `company123` |
| User | `user@example.com` | `user123` |
| User | `alice@example.com` | `alice123` |
| User | `bob@example.com` | `bob123` |

---

## Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+

### 1. Clone & Install Backend

```bash
cd server
pip install -r requirements.txt
```

### 2. Install & Build Frontend

```bash
cd frontend
npm install
npm run build
```

### 3. Run the Server

```bash
# From project root
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

The frontend is served from `http://localhost:8000` (FastAPI serves the Vite `dist/` build as static files).

### 4. Development Mode (Frontend Hot Reload)

```bash
# Terminal 1 — backend
uvicorn server.app:app --reload

# Terminal 2 — frontend dev server
cd frontend
npm run dev
```

Frontend dev server proxies API calls to `localhost:8000` via Vite config.

---

## Project Structure

```
phantomV2Lat/
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.jsx            # Landing page
│   │   │   ├── Login.jsx           # Auth (login + register)
│   │   │   ├── AdminDashboard.jsx  # SOC dashboard (admin only)
│   │   │   ├── CompanyDashboard.jsx# Company-level view
│   │   │   ├── UserView.jsx        # User interface + attack surface
│   │   │   └── ValidationLab.jsx   # Attack validation tests
│   │   ├── components/             # Reusable UI components
│   │   ├── utils/api.js            # API client
│   │   └── index.css               # Design system
│   └── dist/                       # Production build (served by FastAPI)
│
├── server/
│   ├── app.py                      # FastAPI entry point + WebSocket + auth
│   ├── ml_engine.py                # LightGBM inference pipeline
│   ├── soc_engine.py               # Kill chain tracker (MITRE ATT&CK)
│   ├── database.py                 # SQLAlchemy models + SQLite
│   ├── auth.py                     # JWT auth, user management
│   ├── middleware.py               # IP block middleware + blocked_ips set
│   ├── realtime.py                 # WebSocket broadcast manager
│   ├── alerts.py                   # Twilio SMS + Voice integration
│   ├── cdl/
│   │   ├── core.py                 # AttackerMemory — per-IP tracking
│   │   ├── predictor.py            # Next-move predictor
│   │   ├── countermeasures.py      # Automated countermeasure selector
│   │   └── engine.py               # CDL orchestration engine
│   └── routes/
│       ├── website.py              # XYZ target site + all 5 attack detectors
│       ├── admin.py                # Admin API (logs, alerts, blocked IPs)
│       ├── company.py              # Company dashboard API
│       ├── honeypot.py             # Honeypot endpoints
│       ├── validation.py           # Validation lab API
│       ├── soc.py                  # SOC intelligence API
│       └── logs.py                 # Request log API
│
├── models/                         # Trained model artifacts
│   ├── lgbm_model.pkl
│   ├── scaler.pkl
│   ├── feature_selector.pkl
│   └── feature_columns.pkl
│
└── phantom.db                      # SQLite database
```

---

## ML Model Details

| Property | Value |
|---|---|
| **Model** | LightGBM (Gradient Boosted Trees) |
| **Tuning** | Optuna Bayesian hyperparameter search |
| **Dataset** | UNSW-NB15 (2.5M+ network flow records) |
| **Task** | Binary classification — normal vs. attack |
| **Attack Categories** | Brute Force, DoS, Exploits, Reconnaissance, Backdoors, Worms, Shellcode, Fuzzers, Analysis, Generic |
| **Feature Count** | 200+ (engineered from raw PCAP fields) |
| **Preprocessing** | MinMaxScaler → feature selector → LightGBM |
| **Threshold** | `predict_proba() > 0.85` → classified as attack |

---

## Attack Detection Logic

Each of the 5 attack types uses a different detection mechanism, all feeding into the same ML pipeline:

```
User Input / Request
       │
       ▼
┌─────────────────────┐
│  Pattern Detection   │  ← SQL regex, XSS regex, rate counter, enumeration count
└─────────────────────┘
       │ match
       ▼
┌─────────────────────┐
│  ML Event Generator  │  ← synthetic UNSW-NB15 event (attack_probability scales with severity)
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│  LightGBM Inference  │  ← predict_proba() → confidence score
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│  CDL Engine          │  ← risk score = model_conf × 0.70 + attempt_pressure × 0.30
└─────────────────────┘
       │ risk ≥ threshold
       ▼
   Auto-Block + Alert + WebSocket Broadcast + (optional) Twilio SMS
```

### Brute Force — ML-Driven Tiers
Unlike a hard counter rule, the brute force detection uses the model's confidence to decide:

| CDL Risk Score | Response |
|---|---|
| `< 0.35` (attempts 1–2) | Silent fail — no warning shown |
| `0.35 – 0.74` (attempts 3–4) | ⚠️ Suspicious warning banner |
| `≥ 0.75` (attempt 5+) | 🚫 IP blocked, critical alert fired |

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Authenticate user, get JWT |
| `POST` | `/api/auth/register` | Register new user |
| `GET` | `/api/auth/me` | Get current user info |
| `POST` | `/api/xyz/login` | XYZ login (brute force + SQL injection target) |
| `GET` | `/api/xyz/data` | Fetch data (DDoS rate-detection target) |
| `POST` | `/api/xyz/form` | Contact form (XSS target) |
| `POST` | `/api/xyz/flood` | DDoS flood simulation endpoint |
| `POST` | `/api/xyz/probe` | Port scan / endpoint enumeration |
| `POST` | `/api/xyz/attack` | Manual attack simulation (Attack Panel) |
| `GET` | `/api/xyz/my-ip` | Get current user's assigned simulated IP |
| `GET` | `/api/admin/logs` | All request logs (admin) |
| `GET` | `/api/admin/alerts` | All alerts (admin) |
| `GET` | `/api/admin/blocked` | Blocked IPs list |
| `POST` | `/api/admin/unblock/{ip}` | Unblock an IP |
| `POST` | `/api/reset` | Full system reset (clears all logs + IPs) |
| `GET` | `/api/twilio/status` | Twilio toggle state |
| `POST` | `/api/twilio/toggle` | Toggle Twilio SMS/Voice on/off |
| `WS` | `/ws` | WebSocket — real-time event stream |
| `GET` | `/api/health` | Health check + ML model status |

---

## System Reset

A **System Reset** button is available on the Login page. It clears all request logs, alerts, blocked IPs, and honeypot events — useful between hackathon demo runs. Default accounts and passwords are re-seeded automatically.

---

## Twilio Alerts (Optional)

When enabled via the toggle in the Admin dashboard, PHANTOM sends:
- 📱 **SMS** to the admin phone with attack type, IP, and confidence score
- 📞 **Voice call** with a synthesized alert message

Configure credentials in `server/alerts.py`.

---

*Built with ❤️ for the Hack Malenadu '26 Hackathon.*
