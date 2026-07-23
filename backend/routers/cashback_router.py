from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import math

from backend.dependencies import get_db, get_current_user
from backend.models import User
from backend.schemas import CashbackTransactionResponse, PaginatedResponse
from backend.repositories.cashback_repository import CashbackRepository

router = APIRouter(prefix="/api/cashback", tags=["Cashback Analytics"])

@router.get("/history", response_model=PaginatedResponse[CashbackTransactionResponse])
def get_cashback_history(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves all cashback conversion records for the current user."""
    repo = CashbackRepository(db)
    skip = (page - 1) * limit
    items, total = repo.get_by_user_id(current_user.id, status=None, skip=skip, limit=limit)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    return PaginatedResponse(items=items, total=total, page=page, limit=limit, total_pages=total_pages)

@router.get("/pending", response_model=PaginatedResponse[CashbackTransactionResponse])
def get_pending_cashback(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves pending cashback conversion records for the current user."""
    repo = CashbackRepository(db)
    skip = (page - 1) * limit
    items, total = repo.get_by_user_id(current_user.id, status="pending", skip=skip, limit=limit)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    return PaginatedResponse(items=items, total=total, page=page, limit=limit, total_pages=total_pages)

@router.get("/approved", response_model=PaginatedResponse[CashbackTransactionResponse])
def get_approved_cashback(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves approved cashback conversion records for the current user."""
    repo = CashbackRepository(db)
    skip = (page - 1) * limit
    items, total = repo.get_by_user_id(current_user.id, status="approved", skip=skip, limit=limit)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    return PaginatedResponse(items=items, total=total, page=page, limit=limit, total_pages=total_pages)
