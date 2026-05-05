# SmishGuard — Python FastAPI Backend
## Production-Ready SMS Phishing Detection API

---

## Overview

This is the backend server for the SmishGuard Android application. It exposes a REST API that accepts an incoming SMS message and returns a phishing/ham classification. The analysis logic lives in a single service file — swap out the placeholder with your real ML model without touching any route code.

---

## Project Structure

```
sms-detection-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point, CORS, routers
│   ├── routes/
│   │   ├── __init__.py
│   │   └── sms.py               # POST /analyze-sms route
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── sms.py               # Pydantic request / response models
│   └── services/
│       ├── __init__.py
│       └── sms_analyzer.py      # ← PLUG YOUR ML MODEL IN HERE
├── requirements.txt
├── Procfile                     # Render / Heroku start command
├── .gitignore
└── README.md
```

---

## API Endpoints

### GET /
Returns a basic status message confirming the API is running.

**Response**
```json
{
  "message": "SmishGuard API is running",
  "version": "1.0.0"
}
```

---

### GET /health
Health-check endpoint. Used by deployment platforms (Render, Railway, etc.) to verify the service is alive.

**Response**
```json
{
  "status": "ok"
}
```

---

### POST /analyze-sms
Main endpoint. The Android app sends each incoming SMS here and receives a classification result.

**Request**
```
POST /analyze-sms
Content-Type: application/json

{
  "message": "URGENT: Your account is locked. Click http://bit.ly/unlock to verify."
}
```

**Response — Smishing detected**
```json
{
  "is_smishing": true,
  "confidence": 0.91,
  "label": "smishing",
  "reason": "Placeholder: matched keyword(s): urgent, click, verify, account"
}
```

**Response — Safe (ham)**
```json
{
  "is_smishing": false,
  "confidence": 0.05,
  "label": "ham",
  "reason": "Placeholder: no suspicious keywords detected"
}
```

**Validation error (empty message)**
```json
{
  "detail": "message must not be empty"
}
```

---

## File-by-File Reference

### `app/main.py`
FastAPI application factory. Registers CORS middleware (allows all origins for Android compatibility), mounts routers, and defines the root `GET /` endpoint.

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import sms

app = FastAPI(title="SmishGuard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten to your domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sms.router)

@app.get("/")
def root():
    return {"message": "SmishGuard API is running", "version": "1.0.0"}

@app.get("/health")
def health():
    return {"status": "ok"}
```

---

### `app/schemas/sms.py`
Pydantic models for request validation and response serialization.

```python
from pydantic import BaseModel, field_validator

class SMSRequest(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def message_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be empty")
        return v.strip()

class SMSResponse(BaseModel):
    is_smishing: bool
    confidence: float
    label: str
    reason: str
```

---

### `app/routes/sms.py`
Route handler. Calls the analyzer service and returns the result. No business logic here.

```python
from fastapi import APIRouter
from app.schemas.sms import SMSRequest, SMSResponse
from app.services.sms_analyzer import analyze_sms

router = APIRouter()

@router.post("/analyze-sms", response_model=SMSResponse)
def analyze(request: SMSRequest) -> SMSResponse:
    result = analyze_sms(request.message)
    return SMSResponse(
        is_smishing=result.is_smishing,
        confidence=result.confidence,
        label=result.label,
        reason=result.reason,
    )
```

---

### `app/services/sms_analyzer.py`
**This is the only file you need to edit when swapping in your real model.**

```python
# ---------------------------------------------------------------
# PLUG YOUR ML MODEL IN HERE
# ---------------------------------------------------------------
# 1. Load your model at module level:
#    import joblib
#    model      = joblib.load("models/smishing_detector.pkl")
#    vectorizer = joblib.load("models/tfidf_vectorizer.pkl")
#
# 2. Replace the body of analyze_sms() with your inference code.
#    Return an AnalysisResult — the route does not change.
# ---------------------------------------------------------------

from dataclasses import dataclass

SMISHING_KEYWORDS = {
    "urgent", "verify", "account locked", "click", "payment failed",
    "suspended", "confirm", "login", "bank", "free", "win", "prize",
}

@dataclass
class AnalysisResult:
    is_smishing: bool
    confidence: float
    label: str
    reason: str

def analyze_sms(message: str) -> AnalysisResult:
    lowered = message.lower()
    matched = [kw for kw in SMISHING_KEYWORDS if kw in lowered]
    if matched:
        confidence = min(0.60 + len(matched) * 0.08, 0.99)
        return AnalysisResult(True, round(confidence, 2), "smishing",
                              f"Matched: {', '.join(matched)}")
    return AnalysisResult(False, 0.05, "ham", "No suspicious keywords")
```

---

### `requirements.txt`

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
pydantic==2.9.2
```

> When you add your real model, append its dependencies:
> ```
> scikit-learn==1.5.2
> sentence-transformers==3.1.1
> joblib==1.4.2
> xgboost==2.1.1
> ```

---

### `Procfile`

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Render and Railway read this automatically. `$PORT` is injected by the platform.

---

### `.gitignore`

```
__pycache__/
*.py[cod]
*.pkl
*.joblib
.env
venv/
.venv/
*.egg-info/
dist/
build/
.DS_Store
```

---

## Local Setup

```bash
# 1. Clone / enter the project
cd sms-detection-backend

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the development server
uvicorn app.main:app --reload --port 8000
```

The API is now available at `http://localhost:8000`.
Interactive docs (Swagger UI): `http://localhost:8000/docs`

---

## Example curl Requests

```bash
# Health check
curl http://localhost:8000/health

# Analyze a smishing SMS
curl -X POST http://localhost:8000/analyze-sms \
  -H "Content-Type: application/json" \
  -d '{"message": "URGENT: Your account is suspended. Click here to verify."}'

# Analyze a safe SMS
curl -X POST http://localhost:8000/analyze-sms \
  -H "Content-Type: application/json" \
  -d '{"message": "Hey, are we still meeting at 6pm today?"}'
```

---

## Android App Integration

| Environment | Base URL |
|---|---|
| Android Emulator → localhost | `http://10.0.2.2:8000` |
| Real device on same Wi-Fi | `http://<your-laptop-IP>:8000` |
| After deploying to Render | `https://your-app-name.onrender.com` |

In the Android app (Retrofit):
```kotlin
// Local development (emulator)
const val BASE_URL = "http://10.0.2.2:8000/"

// Production (after deployment)
const val BASE_URL = "https://your-app-name.onrender.com/"
```

> **Note:** Android blocks plain HTTP by default for real-device testing.
> Either use HTTPS (production URL) or add a `network_security_config.xml`
> that allows cleartext traffic for your local IP only.

---

## Deployment to Render (Free Tier)

1. Push the project to a GitHub repository.
2. Log in to [render.com](https://render.com) and click **New → Web Service**.
3. Connect your GitHub repository.
4. Set the following:

| Setting | Value |
|---|---|
| Environment | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

5. Click **Create Web Service** — Render detects `Procfile` automatically.
6. Your API URL will be: `https://your-app-name.onrender.com`

---

## Plugging In Your Real ML Model

Only `app/services/sms_analyzer.py` needs to change:

| Step | What to do |
|---|---|
| 1 | Copy your `.pkl` / `.joblib` model files into a `models/` folder |
| 2 | Load them at module level with `joblib.load(...)` |
| 3 | Replace the body of `analyze_sms()` with your inference pipeline |
| 4 | Add model dependencies to `requirements.txt` |
| 5 | Re-deploy — the route, schema, and Android app stay identical |

Your existing inference code from `NLP_smish.py` / `runModel.py` can be
pasted directly into `analyze_sms()` with minimal changes.

---

## Error Handling Summary

| Scenario | HTTP Status | Response |
|---|---|---|
| Empty message body | 422 | `{"detail": "message must not be empty"}` |
| Missing `message` field | 422 | FastAPI automatic validation error |
| Internal analyzer exception | 500 | `{"detail": "Internal server error"}` |
| Unknown route | 404 | FastAPI automatic 404 |
