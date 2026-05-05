from fastapi import APIRouter, HTTPException
from app.schemas.sms import SMSRequest, SMSResponse
from app.services.sms_analyzer import analyze_sms

router = APIRouter()


@router.post("/analyze-sms", response_model=SMSResponse)
def analyze(request: SMSRequest) -> SMSResponse:
    try:
        result = analyze_sms(request.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    return SMSResponse(
        is_smishing=result.is_smishing,
        confidence=result.confidence,
        label=result.label,
        reason=result.reason,
    )
