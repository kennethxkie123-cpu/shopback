from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from backend.core.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user", index=True, nullable=False) # user, admin

    wallet_balance = Column(Numeric(12, 2), default=0.00, nullable=False)
    wallet_pending = Column(Numeric(12, 2), default=0.00, nullable=False)
    wallet_paid = Column(Numeric(12, 2), default=0.00, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    is_flagged = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)

    affiliate_links = relationship("AffiliateLink", back_populates="user")
    cashback_transactions = relationship("CashbackTransaction", back_populates="user")
    wallet_transactions = relationship("WalletTransaction", back_populates="user")
    withdrawal_requests = relationship("WithdrawalRequest", back_populates="user")
    fraud_logs = relationship("FraudLog", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

class AffiliateLink(Base):
    __tablename__ = "affiliate_links"

    id = Column(Integer, primary_key=True, index=True)
    tracking_id = Column(String(64), unique=True, index=True, nullable=False)
    
    aff_sub1 = Column(String(64), index=True, nullable=True) # tracking_id
    aff_sub2 = Column(String(64), index=True, nullable=True) # user_id
    aff_sub3 = Column(String(64), index=True, nullable=True) # app_name
    aff_sub4 = Column(String(64), index=True, nullable=True) # platform
    aff_sub5 = Column(String(64), index=True, nullable=True) # app_version

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    offer_id = Column(Integer, index=True, nullable=False)
    original_url = Column(Text, nullable=False)
    deeplink = Column(Text, nullable=False)
    
    status = Column(String(30), default="generated", index=True, nullable=False)
    # generated, clicked, tracked, pending, approved, rejected, cancelled, paid, expired

    clicks = Column(Integer, default=0, nullable=False)
    conversion_id = Column(String(100), index=True, nullable=True)
    order_id = Column(String(100), index=True, nullable=True)

    estimated_commission = Column(Numeric(12, 2), default=0.00, nullable=False)
    approved_commission = Column(Numeric(12, 2), default=0.00, nullable=False)
    cashback_amount = Column(Numeric(12, 2), default=0.00, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="affiliate_links")
    cashback_transactions = relationship("CashbackTransaction", back_populates="affiliate_link")

class CashbackSetting(Base):
    __tablename__ = "cashback_settings"

    id = Column(Integer, primary_key=True, index=True)
    merchant = Column(String(100), unique=True, index=True, nullable=False) # Shopee, Lazada, TikTok, Default
    cashback_percentage = Column(Numeric(5, 2), nullable=False) # e.g. 80.00 for 80%
    effective_date = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    active = Column(Boolean, default=True, index=True, nullable=False)

class CashbackTransaction(Base):
    __tablename__ = "cashback_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    affiliate_link_id = Column(Integer, ForeignKey("affiliate_links.id", ondelete="SET NULL"), nullable=True)

    tracking_id = Column(String(64), index=True, nullable=False)
    aff_sub1 = Column(String(64), index=True, nullable=True)
    aff_sub2 = Column(String(64), index=True, nullable=True)
    aff_sub3 = Column(String(64), index=True, nullable=True)
    aff_sub4 = Column(String(64), index=True, nullable=True)
    aff_sub5 = Column(String(64), index=True, nullable=True)

    conversion_id = Column(String(100), unique=True, index=True, nullable=False)
    order_id = Column(String(100), index=True, nullable=True)
    merchant = Column(String(100), index=True, nullable=True)

    commission = Column(Numeric(12, 2), default=0.00, nullable=False)
    cashback = Column(Numeric(12, 2), default=0.00, nullable=False)
    status = Column(String(30), default="pending", index=True, nullable=False) # pending, approved, rejected, cancelled, paid

    created_at = Column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="cashback_transactions")
    affiliate_link = relationship("AffiliateLink", back_populates="cashback_transactions")

class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Ledger Types: cashback_pending, cashback_approved, cashback_reversed, withdrawal_request, withdrawal_paid, manual_adjustment, refund
    type = Column(String(50), index=True, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    
    reference = Column(String(255), nullable=True)
    conversion_id = Column(String(100), index=True, nullable=True)
    tracking_id = Column(String(64), index=True, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)

    user = relationship("User", back_populates="wallet_transactions")

class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(30), default="Pending", index=True, nullable=False) # Pending, Approved, Rejected, Paid

    bank_account = Column(String(100), nullable=True)
    payment_method = Column(String(50), default="Bank Transfer", nullable=False)
    reference = Column(String(255), nullable=True)

    requested_at = Column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="withdrawal_requests")

class FraudLog(Base):
    __tablename__ = "fraud_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    
    event_type = Column(String(50), index=True, nullable=False) # rate_limit_exceeded, duplicate_url_abuse, suspicious_ip
    description = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=True)
    metadata_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)

    user = relationship("User", back_populates="fraud_logs")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    
    type = Column(String(50), index=True, nullable=False) # link_created, purchase_tracked, cashback_pending, cashback_approved, withdrawal_paid, cashback_rejected
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False, index=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, index=True, nullable=False)

    user = relationship("User", back_populates="notifications")

class CashbackPolicy(Base):
    __tablename__ = "cashback_policies"

    id = Column(Integer, primary_key=True, index=True)
    merchant = Column(String(100), unique=True, index=True, nullable=False)
    
    cashback_type = Column(String(50), default="percentage", nullable=False) # percentage, fixed, tiered
    cashback_value = Column(Numeric(10, 2), default=Decimal("20.00"), nullable=False)
    minimum_cashback = Column(Numeric(10, 2), nullable=True)
    maximum_cashback = Column(Numeric(10, 2), nullable=True)
    tier_config_json = Column(Text, nullable=True) # JSON list for tiered thresholds
    
    effective_date = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    active = Column(Boolean, default=True, index=True, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
