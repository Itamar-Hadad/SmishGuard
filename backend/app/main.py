import sys
import os

# When run directly (`python3 app/main.py`), Python puts app/ on sys.path.
# Insert the project root (sms-detection-backend/) so `from app.X` imports work.
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import sms

app = FastAPI(title="SmishGuard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
