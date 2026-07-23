from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from typing import Optional

from backend.repositories.affiliate_repository import AffiliateRepository
from backend.repositories.fraud_repository import FraudRepository
from backend.repositories.user_repository import UserRepository
from backend.core.config import settings

class FraudService:
    def __init__(self, db: Session):
        self.db = db
        self.affiliate_repo = AffiliateRepository(db)
        self.fraud_repo = FraudRepository(db)
        self.user_repo = UserRepository(db)

    def validate_link_generation(self, user_id: int, original_url: str, ip_address: Optional[str] = None):
        """
        Validates link generation rules:
        1. Checks if user is flagged/banned.
        2. Checks max links per minute limit.
        3. Checks max links per day limit.
        4. Checks for rapid duplicate URL abuse within 1 minute.
        """
        user = self.user_repo.get_by_id(user_id)
        if user and user.is_flagged:
            self.fraud_repo.log_event(
                user_id=user_id,
                event_type="blocked_user_attempt",
                description="Flagged user attempted link generation",
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been flagged for review. Contact support."
            )

        now = datetime.now(timezone.utc)
        one_min_ago = now - timedelta(minutes=1)
        one_day_ago = now - timedelta(days=1)

        # 1. Links in last minute
        min_count = self.affiliate_repo.count_links_created_since(user_id, one_min_ago)
        if min_count >= settings.MAX_LINKS_PER_MINUTE:
            self.fraud_repo.log_event(
                user_id=user_id,
                event_type="rate_limit_minute_exceeded",
                description=f"User exceeded {settings.MAX_LINKS_PER_MINUTE} links/min rate limit",
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {settings.MAX_LINKS_PER_MINUTE} links allowed per minute."
            )

        # 2. Links in last 24h
        day_count = self.affiliate_repo.count_links_created_since(user_id, one_day_ago)
        if day_count >= settings.MAX_LINKS_PER_DAY:
            self.fraud_repo.log_event(
                user_id=user_id,
                event_type="rate_limit_day_exceeded",
                description=f"User exceeded {settings.MAX_LINKS_PER_DAY} links/day limit",
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily link generation limit ({settings.MAX_LINKS_PER_DAY}) reached."
            )

        # 3. Duplicate URL spamming check (more than 3 identical URLs in 1 min)
        dup_count = self.affiliate_repo.find_duplicate_url_count(user_id, original_url, one_min_ago)
        if dup_count >= 3:
            self.fraud_repo.log_event(
                user_id=user_id,
                event_type="duplicate_url_abuse",
                description=f"User generated duplicate URL {dup_count} times in 1 min",
                ip_address=ip_address,
                metadata_json=f'{{"url": "{original_url}"}}'
            )
