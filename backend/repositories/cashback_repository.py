from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from backend.models import CashbackTransaction

class CashbackRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_conversion_id(self, conversion_id: str) -> Optional[CashbackTransaction]:
        return self.db.query(CashbackTransaction).filter(
            CashbackTransaction.conversion_id == conversion_id
        ).first()

    def get_by_user_id(self, user_id: int, status: Optional[str] = None, skip: int = 0, limit: int = 20) -> Tuple[List[CashbackTransaction], int]:
        query = self.db.query(CashbackTransaction).filter(CashbackTransaction.user_id == user_id)
        if status:
            query = query.filter(CashbackTransaction.status == status)
        total = query.count()
        items = query.order_by(CashbackTransaction.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_all(self, skip: int = 0, limit: int = 50) -> Tuple[List[CashbackTransaction], int]:
        query = self.db.query(CashbackTransaction)
        total = query.count()
        items = query.order_by(CashbackTransaction.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def create(self, txn: CashbackTransaction) -> CashbackTransaction:
        self.db.add(txn)
        self.db.commit()
        self.db.refresh(txn)
        return txn
