from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from backend.models import Notification

logger = logging.getLogger(__name__)

def create_user_notification(
    db: Session,
    user_id: int,
    notification_type: str,
    title: str,
    message: str
) -> Notification:
    """Creates a user notification log entry."""
    notif = Notification(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    logger.info(f"Notification created for User #{user_id}: [{notification_type}] {title}")
    return notif

def get_user_notifications(db: Session, user_id: int, limit: int = 20) -> List[Notification]:
    """Retrieves recent notifications for a specific user."""
    return db.query(Notification).filter(
        Notification.user_id == user_id
    ).order_by(Notification.created_at.desc()).limit(limit).all()

def mark_notification_read(db: Session, notification_id: int, user_id: int) -> bool:
    """Marks a notification as read."""
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == user_id
    ).first()
    if notif:
        notif.read = True
        db.commit()
        return True
    return False
