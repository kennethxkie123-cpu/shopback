import sys
import os
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.database import engine, Base, SessionLocal
from backend.models import User, CashbackSetting
from backend.core.security import hash_password

logger = logging.getLogger(__name__)

def seed_data(db: Session):
    """Performs database seeding for demo user, admin user, and cashback settings."""
    # 1. Seed Demo User (John Cashback)
    demo_email = "john@example.com"
    demo_user = db.query(User).filter(User.email == demo_email).first()
    if not demo_user:
        logger.info(f"Seeding demo user: John Cashback ({demo_email})...")
        demo_user = User(
            name="John Cashback",
            email=demo_email,
            password_hash=hash_password("Password123"),
            role="user",
            wallet_balance=Decimal("0.00"),
            wallet_pending=Decimal("0.00"),
            wallet_paid=Decimal("0.00")
        )
        db.add(demo_user)

    # 2. Seed Admin User
    admin_email = "admin@example.com"
    admin_user = db.query(User).filter(User.email == admin_email).first()
    if not admin_user:
        logger.info(f"Seeding admin user ({admin_email})...")
        admin_user = User(
            name="System Admin",
            email=admin_email,
            password_hash=hash_password("Admin123!"),
            role="admin",
            wallet_balance=Decimal("0.00"),
            wallet_pending=Decimal("0.00"),
            wallet_paid=Decimal("0.00")
        )
        db.add(admin_user)

    # 3. Seed Merchant Cashback Settings (10% User Cashback, 90% Admin Profit)
    default_settings = [
        ("Shopee", Decimal("10.00")),
        ("Lazada", Decimal("10.00")),
        ("TikTok", Decimal("10.00")),
        ("Default", Decimal("10.00")),
    ]
    for merchant, percentage in default_settings:
        setting = db.query(CashbackSetting).filter(CashbackSetting.merchant == merchant).first()
        if not setting:
            logger.info(f"Seeding cashback setting for {merchant}: {percentage}% (10% User, 90% Admin)")
            db.add(CashbackSetting(merchant=merchant, cashback_percentage=percentage, active=True))
        else:
            # Update existing setting to 10%
            setting.cashback_percentage = percentage
            setting.active = True

    db.commit()
    logger.info("Database seeding completed successfully.")

def init_db():
    """Creates database tables and seeds initial data. Auto-heals outdated SQLite schema columns."""
    logger.info("Initializing production database schema...")
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        seed_data(db)
    except OperationalError as oe:
        logger.warning(f"Database schema mismatch detected ({oe}). Recreating database tables...")
        db.rollback()
        db.close()
        
        # Drop outdated schema and recreate fresh tables
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        seed_data(db)
    except Exception as e:
        logger.error(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
