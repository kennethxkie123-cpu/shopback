import os
import sys
import uuid
import pytest
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.database import SessionLocal, engine, Base
from backend.seed import init_db
from backend.models import User, AffiliateLink, CashbackTransaction, WalletTransaction, WithdrawalRequest, FraudLog, CashbackSetting
from backend.schemas import ConversionCallbackPayload
from backend.services.affiliate_service import generate_user_affiliate_link
from backend.services.cashback_service import process_conversion_callback
from backend.services.wallet_service import (
    get_user_wallet_summary,
    create_withdrawal_request,
    approve_withdrawal_request,
    reject_withdrawal_request
)
from backend.services.fraud_service import FraudService
from backend.repositories.wallet_repository import WalletRepository
from backend.repositories.settings_repository import SettingsRepository
from backend.repositories.affiliate_repository import AffiliateRepository
from fastapi import HTTPException

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite:///./test_app.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    db = TestSessionLocal()
    try:
        from backend.models import User, CashbackSetting
        from backend.core.security import hash_password
        
        # Seed test user
        user = User(
            name="John Cashback",
            email="john@example.com",
            password_hash=hash_password("Password123"),
            role="user",
            wallet_balance=Decimal("0.00"),
            wallet_pending=Decimal("0.00"),
            wallet_paid=Decimal("0.00")
        )
        db.add(user)

        # Seed admin user
        admin = User(
            name="Admin User",
            email="admin@example.com",
            password_hash=hash_password("Admin123!"),
            role="admin",
            wallet_balance=Decimal("0.00"),
            wallet_pending=Decimal("0.00"),
            wallet_paid=Decimal("0.00")
        )
        db.add(admin)

        # Seed settings (20% User Cashback, 80% Admin Profit)
        db.add(CashbackSetting(merchant="Shopee", cashback_percentage=Decimal("20.00"), active=True))
        db.add(CashbackSetting(merchant="Lazada", cashback_percentage=Decimal("20.00"), active=True))
        db.add(CashbackSetting(merchant="TikTok", cashback_percentage=Decimal("20.00"), active=True))
        db.add(CashbackSetting(merchant="Default", cashback_percentage=Decimal("20.00"), active=True))

        db.commit()
    finally:
        db.close()
    yield

@pytest.fixture
def db():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_decimal_money_precision_and_merchant_settings(db):
    """Verifies that money is represented as Decimal and dynamic merchant rates are applied."""
    settings_repo = SettingsRepository(db)
    
    shopee_rate = settings_repo.get_cashback_rate("Shopee")
    lazada_rate = settings_repo.get_cashback_rate("Lazada")
    tiktok_rate = settings_repo.get_cashback_rate("TikTok")

    assert shopee_rate == Decimal("0.20")
    assert lazada_rate == Decimal("0.20")
    assert tiktok_rate == Decimal("0.20")

def test_full_conversion_lifecycle_and_idempotency(db):
    """Tests sub-tracking, pending -> approved lifecycle, duplicate callback safety, and ledger SUM."""
    user = db.query(User).filter(User.email == "john@example.com").first()
    assert user is not None

    # Clean user wallet state
    user.wallet_balance = Decimal("0.00")
    user.wallet_pending = Decimal("0.00")
    user.wallet_paid = Decimal("0.00")
    db.commit()

    # 1. Generate link with sub-tracking
    product_url = "https://shopee.ph/product/test/123"
    aff_link = generate_user_affiliate_link(db, user, product_url)
    
    assert aff_link.aff_sub1 == aff_link.tracking_id
    assert aff_link.aff_sub2 == str(user.id)
    assert aff_link.aff_sub3 == "shopback"
    assert aff_link.aff_sub4 == "web"
    assert aff_link.aff_sub5 == "v2.0"

    tracking_id = aff_link.tracking_id
    conversion_id = f"CONV_TEST_{uuid.uuid4().hex[:6]}"

    # 2. Incoming Pending Callback (Commission = PHP 300.00 -> 20% User Cashback = PHP 60.00)
    payload_pending = ConversionCallbackPayload(
        conversion_id=conversion_id,
        order_id="SP999111",
        status="pending",
        commission=Decimal("300.00"),
        merchant="Shopee",
        aff_sub1=tracking_id,
        aff_sub2=str(user.id)
    )

    txn_pending = process_conversion_callback(db, payload_pending)
    db.refresh(user)

    assert txn_pending.cashback == Decimal("60.00")
    assert user.wallet_pending == Decimal("60.00")
    assert user.wallet_balance == Decimal("0.00")

    # 3. Test Idempotent Duplicate Callback
    txn_dup = process_conversion_callback(db, payload_pending)
    db.refresh(user)
    assert user.wallet_pending == Decimal("60.00"), "Duplicate callback must not inflate pending balance"

    # 4. Incoming Approved Callback (Pending -> Approved)
    payload_approved = ConversionCallbackPayload(
        conversion_id=conversion_id,
        order_id="SP999111",
        status="approved",
        commission=Decimal("300.00"),
        merchant="Shopee",
        aff_sub1=tracking_id,
        aff_sub2=str(user.id)
    )

    txn_approved = process_conversion_callback(db, payload_approved)
    db.refresh(user)

    assert user.wallet_pending == Decimal("0.00")
    assert user.wallet_balance == Decimal("60.00")

    # 5. Ledger Balance Verification
    wallet_repo = WalletRepository(db)
    ledger_derived = wallet_repo.recalculate_wallet_from_ledger(user.id)
    assert ledger_derived["wallet_balance"] == Decimal("60.00")
    assert ledger_derived["wallet_pending"] == Decimal("0.00")

def test_two_step_withdrawal_workflow(db):
    """Tests submission of withdrawal request, admin approval, and ledger entry."""
    user = db.query(User).filter(User.email == "john@example.com").first()
    
    # Ensure user has 50.00 available balance
    wallet_repo = WalletRepository(db)
    ledger_summary = wallet_repo.recalculate_wallet_from_ledger(user.id)
    current_bal = ledger_summary["wallet_balance"]
    assert current_bal >= Decimal("50.00")

    # 1. User submits withdrawal request
    w_req = create_withdrawal_request(
        db=db,
        user=user,
        amount=Decimal("50.00"),
        bank_account="GCash 09171234567",
        payment_method="GCash"
    )
    assert w_req.status == "Pending"

    # 2. Admin approves withdrawal
    approved_w = approve_withdrawal_request(
        db=db,
        withdrawal_id=w_req.id,
        admin_reference="REF_GCASH_998877"
    )
    assert approved_w.status == "Paid"
    
    # Verify balance was updated atomically via ledger
    db.refresh(user)
    new_ledger_summary = wallet_repo.recalculate_wallet_from_ledger(user.id)
    assert new_ledger_summary["wallet_balance"] == current_bal - Decimal("50.00")
    assert new_ledger_summary["wallet_paid"] >= Decimal("50.00")

def test_fraud_service_rate_limiting(db):
    """Tests rate limit enforcement and fraud logging."""
    user = db.query(User).filter(User.email == "john@example.com").first()
    fraud_service = FraudService(db)
    affiliate_repo = AffiliateRepository(db)

    # Insert 10 links in DB to hit rate limit
    for i in range(10):
        affiliate_repo.create(AffiliateLink(
            tracking_id=f"TRK_{i}_{uuid.uuid4().hex[:4]}",
            user_id=user.id,
            offer_id=5034,
            original_url=f"https://shopee.ph/spam{i}",
            deeplink=f"https://invl.me/test{i}"
        ))

    # Ensure rate limit exception is triggered on 11th request
    with pytest.raises(HTTPException) as exc_info:
        fraud_service.validate_link_generation(user.id, "https://shopee.ph/spam11", "127.0.0.1")
    
    assert exc_info.value.status_code in [429, 403]
    
    # Verify FraudLog table record was created
    log = db.query(FraudLog).filter(FraudLog.user_id == user.id).first()
    assert log is not None
