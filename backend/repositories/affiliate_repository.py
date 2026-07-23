from sqlalchemy.orm import Session
from typing import Optional, List, Tuple
from datetime import datetime, timedelta, timezone
from backend.models import AffiliateLink

class AffiliateRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_tracking_id(self, tracking_id: str) -> Optional[AffiliateLink]:
        return self.db.query(AffiliateLink).filter(
            (AffiliateLink.tracking_id == tracking_id) | (AffiliateLink.aff_sub1 == tracking_id)
        ).first()

    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 20) -> Tuple[List[AffiliateLink], int]:
        query = self.db.query(AffiliateLink).filter(AffiliateLink.user_id == user_id)
        total = query.count()
        items = query.order_by(AffiliateLink.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def count_links_created_since(self, user_id: int, since_time: datetime) -> int:
        return self.db.query(AffiliateLink).filter(
            AffiliateLink.user_id == user_id,
            AffiliateLink.created_at >= since_time
        ).count()

    def find_duplicate_url_count(self, user_id: int, original_url: str, since_time: datetime) -> int:
        return self.db.query(AffiliateLink).filter(
            AffiliateLink.user_id == user_id,
            AffiliateLink.original_url == original_url,
            AffiliateLink.created_at >= since_time
        ).count()

    def create(self, link: AffiliateLink) -> AffiliateLink:
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link
