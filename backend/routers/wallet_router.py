from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import math

from backend.dependencies import get_db, get_current_user
from backend.models import User
from backend.schemas import (
    WalletResponse,
    WalletTransactionResponse,
    CreateWithdrawalRequest,
    WithdrawalRequestResponse,
    PaginatedResponse
)
from backend.services.wallet_service import (
    get_user_wallet_summary,
    get_user_wallet_history_paginated,
    create_withdrawal_request
)

router = APIRouter(prefix="/api/wallet", tags=["Wallet Ledger & Withdrawals"])

from backend.models import AffiliateLink
from sqlalchemy import func
from decimal import Decimal

@router.get("", response_model=WalletResponse)
def get_wallet(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Returns wallet metrics derived directly from the immutable transaction ledger."""
    summary = get_user_wallet_summary(db=db, user=current_user)
    est_val = db.query(func.sum(AffiliateLink.cashback_amount)).filter(AffiliateLink.user_id == current_user.id).scalar()
    est_decimal = Decimal(str(est_val)) if est_val is not None else Decimal("0.00")
    return WalletResponse(
        available_balance=summary["wallet_balance"],
        pending_cashback=summary["wallet_pending"],
        total_paid=summary["wallet_paid"],
        estimated_cashback=est_decimal
    )

@router.get("/history", response_model=PaginatedResponse[WalletTransactionResponse])
def get_wallet_history(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns user's paginated wallet transaction ledger."""
    items, total = get_user_wallet_history_paginated(db=db, user_id=current_user.id, page=page, limit=limit)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )

@router.post("/withdraw", response_model=WithdrawalRequestResponse)
def submit_withdrawal_request(
    request: CreateWithdrawalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submits a new withdrawal request for admin approval."""
    req = create_withdrawal_request(
        db=db,
        user=current_user,
        amount=request.amount,
        bank_account=request.bank_account,
        payment_method=request.payment_method
    )
    return req
