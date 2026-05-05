import sys
import os
from dataclasses import dataclass

# Allow importing from the parent project (MLsmish.py lives one level up)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import joblib
from sentence_transformers import SentenceTransformer
from MLsmish import predict_message, SBERT_MODEL_NAME, MODEL_PATH, ENCODER_PATH, TFIDF_PATH

# Load all heavy artifacts once at startup
_model   = joblib.load(os.path.join(_PROJECT_ROOT, MODEL_PATH))
_encoder = joblib.load(os.path.join(_PROJECT_ROOT, ENCODER_PATH))
_tfidf   = joblib.load(os.path.join(_PROJECT_ROOT, TFIDF_PATH))
_sbert   = SentenceTransformer(SBERT_MODEL_NAME)


@dataclass
class AnalysisResult:
    is_smishing: bool
    confidence: float
    label: str
    reason: str


def analyze_sms(message: str) -> AnalysisResult:
    label, confidence = predict_message(
        message,
        model=_model,
        encoder=_encoder,
        sbert=_sbert,
        tfidf=_tfidf,
    )
    is_smishing = label == "smish"
    reason = "ML model classification" if is_smishing else "No smishing pattern detected"
    return AnalysisResult(
        is_smishing=is_smishing,
        confidence=confidence,
        label=label,
        reason=reason,
    )
