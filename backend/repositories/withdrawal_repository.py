from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from backend.models import WithdrawalRequest

class WithdrawalRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, withdrawal_id: int) -> Optional[WithdrawalRequest]:
        return self.db.query(WithdrawalRequest).filter(WithdrawalRequest.id == withdrawal_id).first()

    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 20) -> Tuple[List[WithdrawalRequest], int]:
        query = self.db.query(WithdrawalRequest).filter(WithdrawalRequest.user_id == user_id)
        total = query.count()
        items = query.order_by(WithdrawalRequest.requested_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_all(self, status: Optional[str] = None, skip: int = 0, limit: int = 50) -> Tuple[List[WithdrawalRequest], int]:
        query = self.db.query(WithdrawalRequest)
        if status:
            query = query.filter(WithdrawalRequest.status == status)
        total = query.count()
        items = query.order_by(WithdrawalRequest.requested_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def create(self, request: WithdrawalRequest) -> WithdrawalRequest:
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request
