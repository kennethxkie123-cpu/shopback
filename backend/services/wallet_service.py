import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal
from typing import List, Tuple, Dict, Optional
from datetime import datetime, timezone

from backend.models import User, WalletTransaction, WithdrawalRequest
from backend.repositories.wallet_repository import WalletRepository
from backend.repositories.withdrawal_repository import WithdrawalRepository
from backend.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

def get_user_wallet_summary(db: Session, user: User) -> Dict[str, Decimal]:
    """Derives and verifies user's wallet balances directly from the immutable transaction ledger."""
    wallet_repo = WalletRepository(db)
    summary = wallet_repo.recalculate_wallet_from_ledger(user.id)
    return summary

def create_withdrawal_request(
    db: Session,
    user: User,
    amount: Decimal,
    bank_account: Optional[str] = None,
    payment_method: str = "Bank Transfer"
) -> WithdrawalRequest:
    """
    Submits a user withdrawal request.
    Validates available balance from ledger.
    Does NOT deduct funds immediately until approved by admin.
    """
    if amount <= Decimal("0.00"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Withdrawal amount must be greater than 0"
        )

    wallet_repo = WalletRepository(db)
    ledger_summary = wallet_repo.recalculate_wallet_from_ledger(user.id)
    available_balance = ledger_summary["wallet_balance"]

    if available_balance < amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient available balance. Requested PHP {amount:.2f}, but available balance is PHP {available_balance:.2f}"
        )

    withdrawal_repo = WithdrawalRepository(db)
    req = WithdrawalRequest(
        user_id=user.id,
        amount=amount,
        status="Pending",
        bank_account=bank_account,
        payment_method=payment_method,
        reference=f"WDR_REQ_{user.id}_{int(datetime.now(timezone.utc).timestamp())}"
    )
    saved_req = withdrawal_repo.create(req)
    logger.info(f"User ID={user.id} created WithdrawalRequest ID={saved_req.id} for PHP {amount:.2f}")
    return saved_req

def approve_withdrawal_request(
    db: Session,
    withdrawal_id: int,
    admin_reference: Optional[str] = None
) -> WithdrawalRequest:
    """
    Admin: Approves and marks a withdrawal request as Paid.
    Deducts available balance and adds a 'withdrawal_paid' ledger entry.
    """
    withdrawal_repo = WithdrawalRepository(db)
    user_repo = UserRepository(db)
    wallet_repo = WalletRepository(db)

    req = withdrawal_repo.get_by_id(withdrawal_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Withdrawal request not found")

    if req.status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Withdrawal request is currently in '{req.status}' state and cannot be approved."
        )

    user = user_repo.get_by_id(req.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    ledger_summary = wallet_repo.recalculate_wallet_from_ledger(user.id)
    if ledger_summary["wallet_balance"] < Decimal(str(req.amount)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User has insufficient available balance (PHP {ledger_summary['wallet_balance']:.2f}) for withdrawal of PHP {req.amount:.2f}"
        )

    # Mark Paid
    req.status = "Paid"
    req.processed_at = datetime.now(timezone.utc)
    if admin_reference:
        req.reference = admin_reference

    # Record ledger entry
    wallet_repo.add_ledger_entry(WalletTransaction(
        user_id=user.id,
        type="withdrawal_paid",
        amount=Decimal(str(req.amount)),
        reference=req.reference or f"Approved Withdrawal #{req.id}"
    ))

    db.commit()
    db.refresh(req)

    # Sync summary fields
    wallet_repo.sync_user_wallet_with_ledger(user)
    logger.info(f"Admin approved WithdrawalRequest ID={req.id} for User ID={user.id}. Amount=PHP {req.amount:.2f}")
    return req

def reject_withdrawal_request(
    db: Session,
    withdrawal_id: int,
    reason: Optional[str] = None
) -> WithdrawalRequest:
    """Admin: Rejects a withdrawal request."""
    withdrawal_repo = WithdrawalRepository(db)
    req = withdrawal_repo.get_by_id(withdrawal_id)
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Withdrawal request not found")

    if req.status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Withdrawal request is currently in '{req.status}' state and cannot be rejected."
        )

    req.status = "Rejected"
    req.processed_at = datetime.now(timezone.utc)
    if reason:
        req.reference = f"Rejected: {reason}"

    db.commit()
    db.refresh(req)
    logger.info(f"Admin rejected WithdrawalRequest ID={req.id}. Reason={reason}")
    return req

def get_user_wallet_history_paginated(db: Session, user_id: int, page: int = 1, limit: int = 20) -> Tuple[List[WalletTransaction], int]:
    wallet_repo = WalletRepository(db)
    skip = (page - 1) * limit
    return wallet_repo.get_by_user_id(user_id, skip=skip, limit=limit)

def process_wallet_withdrawal(db: Session, user: User, amount: float | Decimal) -> WithdrawalRequest:
    """Backward compatibility helper for test suites."""
    amt = Decimal(str(amount))
    req = create_withdrawal_request(db=db, user=user, amount=amt)
    approved_req = approve_withdrawal_request(db=db, withdrawal_id=req.id)
    return approved_req

