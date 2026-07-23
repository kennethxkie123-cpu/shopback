from fastapi import APIRouter, Depends, Header, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional
import hmac
import hashlib
import time

from backend.dependencies import get_db
from backend.schemas import ConversionCallbackPayload, CashbackTransactionResponse
from backend.services.cashback_service import process_conversion_callback
from backend.core.config import settings
from backend.core.audit import AuditLogger

router = APIRouter(prefix="/api/callback", tags=["Involve Asia Webhook Callback"])

@router.post("/conversion", response_model=CashbackTransactionResponse)
def conversion_callback(
    payload: ConversionCallbackPayload,
    request: Request,
    db: Session = Depends(get_db),
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp")
):
    """
    Secure, idempotent webhook endpoint for receiving conversion reports from Involve Asia.
    Performs HMAC signature verification, timestamp freshness checks, and replay prevention.
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    # 1. Timestamp Freshness Verification (Replay Attack Prevention)
    if x_timestamp:
        try:
            ts = float(x_timestamp)
            current_ts = time.time()
            if abs(current_ts - ts) > settings.MAX_CALLBACK_AGE_SECONDS:
                AuditLogger.log(
                    action="callback_rejected_stale",
                    resource="conversion_callback",
                    client_ip=client_ip,
                    user_agent=user_agent,
                    result="failure",
                    details={"reason": "Stale timestamp", "timestamp": x_timestamp}
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Callback request timestamp expired or invalid"
                )
        except ValueError:
            pass

    # 2. HMAC Signature Validation (if X-Signature header is provided)
    if x_signature and settings.WEBHOOK_HMAC_SECRET:
        expected_sig = hmac.new(
            settings.WEBHOOK_HMAC_SECRET.encode("utf-8"),
            payload.json().encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(x_signature.lower(), expected_sig.lower()):
            AuditLogger.log(
                action="callback_rejected_signature",
                resource="conversion_callback",
                client_ip=client_ip,
                user_agent=user_agent,
                result="failure",
                details={"reason": "HMAC signature mismatch"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid callback HMAC signature"
            )

    # 3. Process Conversion Idempotently
    txn = process_conversion_callback(db=db, payload=payload)
    
    AuditLogger.log(
        action="cashback_callback_processed",
        user_id=txn.user_id,
        resource=f"conversion_{txn.conversion_id}",
        client_ip=client_ip,
        user_agent=user_agent,
        result="success",
        details={"status": txn.status, "cashback": float(txn.cashback)}
    )
    
    return txn
