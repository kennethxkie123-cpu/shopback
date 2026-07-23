from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
import math

from backend.dependencies import get_db, get_current_admin_user
from backend.models import User
from backend.schemas import (
    UserResponse,
    CashbackTransactionResponse,
    ConversionCallbackPayload,
    WithdrawalRequestResponse,
    ApproveWithdrawalRequest,
    RejectWithdrawalRequest,
    CashbackSettingSchema,
    CashbackSettingCreate,
    AffiliateLinkResponse,
    PaginatedResponse
)
from backend.services.cashback_service import process_conversion_callback
from backend.services.wallet_service import approve_withdrawal_request, reject_withdrawal_request
from backend.repositories.cashback_repository import CashbackRepository
from backend.repositories.user_repository import UserRepository
from backend.repositories.withdrawal_repository import WithdrawalRepository
from backend.repositories.settings_repository import SettingsRepository

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])

@router.get("/users", response_model=PaginatedResponse[UserResponse])
def get_all_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Admin: Returns paginated list of all registered users."""
    from backend.models import AffiliateLink
    from sqlalchemy import func
    
    user_repo = UserRepository(db)
    skip = (page - 1) * limit
    users = user_repo.get_all(skip=skip, limit=limit)
    total = db.query(User).count()
    total_pages = math.ceil(total / limit) if total > 0 else 1

    items = []
    for u in users:
        est_val = db.query(func.sum(AffiliateLink.cashback_amount)).filter(AffiliateLink.user_id == u.id).scalar()
        est_decimal = Decimal(str(est_val)) if est_val is not None else Decimal("0.00")
        
        items.append(UserResponse(
            id=u.id,
            uuid=u.uuid,
            name=u.name,
            email=u.email,
            role=u.role,
            wallet_balance=u.wallet_balance or Decimal("0.00"),
            wallet_pending=u.wallet_pending or Decimal("0.00"),
            wallet_paid=u.wallet_paid or Decimal("0.00"),
            estimated_cashback=est_decimal,
            is_active=u.is_active,
            is_flagged=u.is_flagged,
            created_at=u.created_at
        ))

    return PaginatedResponse(items=items, total=total, page=page, limit=limit, total_pages=total_pages)

@router.get("/users/{user_id}/links", response_model=PaginatedResponse[AffiliateLinkResponse])
def get_user_links_for_admin(
    user_id: int,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Admin: Returns all generated affiliate links for a specific user with full status details."""
    from backend.models import AffiliateLink, User
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    skip = (page - 1) * limit
    total = db.query(AffiliateLink).filter(AffiliateLink.user_id == user_id).count()
    raw_links = db.query(AffiliateLink).filter(AffiliateLink.user_id == user_id).order_by(AffiliateLink.created_at.desc()).offset(skip).limit(limit).all()
    
    items = []
    for link in raw_links:
        link_dto = AffiliateLinkResponse.model_validate(link)
        link_dto.user_name = target_user.name
        items.append(link_dto)

    total_pages = math.ceil(total / limit) if total > 0 else 1
    return PaginatedResponse(items=items, total=total, page=page, limit=limit, total_pages=total_pages)

@router.get("/links", response_model=PaginatedResponse[AffiliateLinkResponse])
def get_all_links(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Admin: Returns paginated list of all generated affiliate links, full user names, and tracking sub IDs."""
    from backend.models import AffiliateLink, User
    skip = (page - 1) * limit
    total = db.query(AffiliateLink).count()
    raw_links = db.query(AffiliateLink).order_by(AffiliateLink.created_at.desc()).offset(skip).limit(limit).all()
    
    items = []
    for link in raw_links:
        user = db.query(User).filter(User.id == link.user_id).first()
        link_dto = AffiliateLinkResponse.model_validate(link)
        link_dto.user_name = user.name if user else f"User #{link.user_id}"
        items.append(link_dto)

    total_pages = math.ceil(total / limit) if total > 0 else 1
    return PaginatedResponse(items=items, total=total, page=page, limit=limit, total_pages=total_pages)

@router.get("/conversions", response_model=PaginatedResponse[CashbackTransactionResponse])
def get_all_conversions(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Admin: Returns paginated list of all conversions."""
    cashback_repo = CashbackRepository(db)
    skip = (page - 1) * limit
    raw_items, total = cashback_repo.get_all(skip=skip, limit=limit)
    
    items = []
    for item in raw_items:
        dto = CashbackTransactionResponse.model_validate(item)
        dto.admin_profit = (item.commission or Decimal("0.00")) - (item.cashback or Decimal("0.00"))
        items.append(dto)

    total_pages = math.ceil(total / limit) if total > 0 else 1
    return PaginatedResponse(items=items, total=total, page=page, limit=limit, total_pages=total_pages)

@router.get("/wallets")
def get_all_wallets(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Admin: Returns wallet summaries for all users."""
    user_repo = UserRepository(db)
    skip = (page - 1) * limit
    users = user_repo.get_all(skip=skip, limit=limit)
    return [
        {
            "user_id": u.id,
            "uuid": u.uuid,
            "name": u.name,
            "email": u.email,
            "wallet_balance": u.wallet_balance,
            "wallet_pending": u.wallet_pending,
            "wallet_paid": u.wallet_paid
        }
        for u in users
    ]

@router.get("/withdrawals", response_model=PaginatedResponse[WithdrawalRequestResponse])
def get_all_withdrawals(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Admin: Returns list of user withdrawal requests."""
    withdrawal_repo = WithdrawalRepository(db)
    skip = (page - 1) * limit
    items, total = withdrawal_repo.get_all(status=status, skip=skip, limit=limit)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    return PaginatedResponse(items=items, total=total, page=page, limit=limit, total_pages=total_pages)

@router.post("/manual-conversion", response_model=CashbackTransactionResponse)
def manual_conversion(
    payload: ConversionCallbackPayload,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Admin Testing Endpoint: Manually trigger/simulate an Involve Asia conversion callback.
    """
    txn = process_conversion_callback(db=db, payload=payload)
    return txn

@router.post("/approve-withdrawal", response_model=WithdrawalRequestResponse)
def approve_withdrawal(
    body: ApproveWithdrawalRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Admin: Approves a user withdrawal request and marks it as Paid."""
    return approve_withdrawal_request(db=db, withdrawal_id=body.withdrawal_id, admin_reference=body.reference)

@router.post("/reject-withdrawal", response_model=WithdrawalRequestResponse)
def reject_withdrawal(
    body: RejectWithdrawalRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Admin: Rejects a user withdrawal request."""
    return reject_withdrawal_request(db=db, withdrawal_id=body.withdrawal_id, reason=body.reason)

@router.post("/cashback-settings", response_model=CashbackSettingSchema)
def create_or_update_cashback_setting(
    body: CashbackSettingCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Admin: Configure merchant cashback rate percentage (e.g. Shopee=80.00, Lazada=75.00)."""
    settings_repo = SettingsRepository(db)
    return settings_repo.create_or_update(
        merchant=body.merchant,
        percentage=body.cashback_percentage,
        active=body.active
    )
