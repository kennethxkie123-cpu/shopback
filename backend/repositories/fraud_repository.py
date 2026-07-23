from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from backend.models import FraudLog

class FraudRepository:
    def __init__(self, db: Session):
        self.db = db

    def log_event(
        self,
        user_id: Optional[int],
        event_type: str,
        description: str,
        ip_address: Optional[str] = None,
        metadata_json: Optional[str] = None
    ) -> FraudLog:
        log = FraudLog(
            user_id=user_id,
            event_type=event_type,
            description=description,
            ip_address=ip_address,
            metadata_json=metadata_json
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_all(self, skip: int = 0, limit: int = 50) -> Tuple[List[FraudLog], int]:
        query = self.db.query(FraudLog)
        total = query.count()
        items = query.order_by(FraudLog.created_at.desc()).offset(skip).limit(limit).all()
        return items, total
