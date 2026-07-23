import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from backend.models import AffiliateLink

logger = logging.getLogger(__name__)

def cleanup_expired_unvalidated_links(db: Session, max_age_hours: int = 24) -> int:
    """
    Deletes generated/unvalidated affiliate links older than 24 hours from the database.
    Does NOT affect approved or paid cashback ledger entries.
    """
    try:
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        # Target unvalidated/pending links older than 24 hours
        query = db.query(AffiliateLink).filter(
            AffiliateLink.status.in_(["generated", "pending", "tracked"]),
            AffiliateLink.created_at <= cutoff_time
        )
        
        deleted_count = query.delete(synchronize_session=False)
        if deleted_count > 0:
            db.commit()
            logger.info(f"Auto-deleted {deleted_count} unvalidated affiliate links older than {max_age_hours} hours.")
        return deleted_count
    except Exception as e:
        logger.error(f"Error executing auto-delete for expired links: {e}")
        db.rollback()
        return 0
