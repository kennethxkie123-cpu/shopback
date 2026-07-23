import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal
from typing import Optional

from backend.models import AffiliateLink, User, CashbackTransaction, WalletTransaction
from backend.schemas import ConversionCallbackPayload
from backend.repositories.affiliate_repository import AffiliateRepository
from backend.repositories.cashback_repository import CashbackRepository
from backend.repositories.user_repository import UserRepository
from backend.repositories.wallet_repository import WalletRepository
from backend.repositories.settings_repository import SettingsRepository

logger = logging.getLogger(__name__)

def process_conversion_callback(db: Session, payload: ConversionCallbackPayload) -> CashbackTransaction:
    """
    Idempotent conversion report processing for Involve Asia webhooks or polling.
    1. Looks up affiliate link via tracking_id (aff_sub1).
    2. Fetches dynamic cashback percentage for merchant from CashbackSetting table.
    3. Calculates cashback using Decimal precision: cashback = commission * merchant_percentage.
    4. Handles status transitions (pending, approved, rejected, cancelled, paid) safely and idempotently.
    5. Inserts immutable wallet ledger entries (cashback_pending, cashback_approved, cashback_reversed).
    6. Re-calculates and verifies user summary wallet metrics directly from ledger SUM.
    7. Fully logged with structured audit trails.
    """
    tracking_id = payload.get_tracking_id()
    if not tracking_id:
        logger.error("Conversion callback missing tracking_id / aff_sub1")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing aff_sub1 or tracking_id parameter")

    affiliate_repo = AffiliateRepository(db)
    cashback_repo = CashbackRepository(db)
    user_repo = UserRepository(db)
    wallet_repo = WalletRepository(db)
    settings_repo = SettingsRepository(db)

    # 1. Search AffiliateLink
    affiliate_link = affiliate_repo.get_by_tracking_id(tracking_id)
    if not affiliate_link:
        logger.error(f"Affiliate link with tracking_id={tracking_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Affiliate link with tracking_id={tracking_id} not found"
        )

    user = user_repo.get_by_id(affiliate_link.user_id)
    if not user:
        logger.error(f"User ID={affiliate_link.user_id} not found")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # 2. Strategy Pattern Cashback Calculation
    from backend.services.cashback_engine import CashbackPolicyEngine
    from backend.services.notification_service import create_user_notification
    from backend.models import CashbackPolicy

    merchant_name = payload.merchant or "Default"
    policy = db.query(CashbackPolicy).filter(
        CashbackPolicy.active == True,
        CashbackPolicy.merchant.ilike(f"%{merchant_name}%")
    ).first()

    p_type = policy.cashback_type if policy else "percentage"
    p_val = policy.cashback_value if policy else Decimal("20.00")
    p_min = policy.minimum_cashback if policy else None
    p_max = policy.maximum_cashback if policy else None

    commission = Decimal(str(payload.commission))
    cashback = CashbackPolicyEngine.calculate_cashback(
        commission=commission,
        policy_type=p_type,
        policy_value=p_val,
        min_cashback=p_min,
        max_cashback=p_max
    )
    new_status = payload.status.lower().strip()

    logger.info(
        f"Processing conversion {payload.conversion_id} | Merchant={merchant_name} | "
        f"PolicyType={p_type} | PolicyVal={p_val} | Commission=PHP {commission} | Cashback=PHP {cashback} | Status={new_status}"
    )

    # 3. Check for existing CashbackTransaction (Idempotency)
    existing_txn = cashback_repo.get_by_conversion_id(payload.conversion_id)

    if existing_txn:
        old_status = existing_txn.status.lower()
        logger.info(f"Existing conversion_id={payload.conversion_id} found. Current status={old_status}, Incoming status={new_status}")
        
        if old_status == new_status:
            logger.info(f"Conversion {payload.conversion_id} already in status '{new_status}'. Idempotent skip.")
            return existing_txn

        # Status transition handling
        old_cashback = Decimal(str(existing_txn.cashback))

        # Ledger Adjustment for Status Transitions
        if old_status == "pending" and new_status == "approved":
            # Pending -> Approved: Move from pending to available
            wallet_repo.add_ledger_entry(WalletTransaction(
                user_id=user.id,
                type="cashback_approved",
                amount=cashback,
                reference=f"Approved conversion {payload.conversion_id}",
                conversion_id=payload.conversion_id,
                tracking_id=tracking_id
            ))
            create_user_notification(
                db, user.id, "cashback_approved",
                "🎉 Cashback Approved!",
                f"Your ₱{cashback} cashback from {merchant_name} has been approved and is ready for withdrawal!"
            )
        elif old_status == "pending" and new_status in ["rejected", "cancelled"]:
            # Pending -> Rejected: Reverse pending cashback
            wallet_repo.add_ledger_entry(WalletTransaction(
                user_id=user.id,
                type="cashback_reversed",
                amount=old_cashback,
                reference=f"Reversed/Rejected conversion {payload.conversion_id}",
                conversion_id=payload.conversion_id,
                tracking_id=tracking_id
            ))
            create_user_notification(
                db, user.id, "cashback_rejected",
                "⚠️ Cashback Cancelled/Rejected",
                f"Unfortunately, your ₱{old_cashback} cashback from {merchant_name} was cancelled by advertiser."
            )
        elif old_status == "approved" and new_status in ["rejected", "cancelled"]:
            # Approved -> Rejected (Correction): Reverse approved cashback
            wallet_repo.add_ledger_entry(WalletTransaction(
                user_id=user.id,
                type="manual_adjustment",
                amount=-old_cashback,
                reference=f"Correction: Cancelled approved conversion {payload.conversion_id}",
                conversion_id=payload.conversion_id,
                tracking_id=tracking_id
            ))

        # Update CashbackTransaction & AffiliateLink
        existing_txn.status = new_status
        existing_txn.commission = commission
        existing_txn.cashback = cashback
        existing_txn.merchant = merchant_name

        affiliate_link.status = new_status
        if new_status == "approved":
            affiliate_link.approved_commission = commission
            affiliate_link.cashback_amount = cashback
        elif new_status == "pending":
            affiliate_link.estimated_commission = commission
            affiliate_link.cashback_amount = cashback

        db.commit()
        db.refresh(existing_txn)

        # Sync user summary balances with Ledger
        wallet_repo.sync_user_wallet_with_ledger(user)
        logger.info(f"Updated conversion {payload.conversion_id} to status '{new_status}'. User wallet synced from ledger.")
        return existing_txn

    # 4. Brand New Conversion Transaction
    txn = CashbackTransaction(
        user_id=user.id,
        affiliate_link_id=affiliate_link.id,
        tracking_id=tracking_id,
        aff_sub1=payload.aff_sub1 or tracking_id,
        aff_sub2=payload.aff_sub2 or str(user.id),
        aff_sub3=payload.aff_sub3 or "shopback",
        aff_sub4=payload.aff_sub4 or "web",
        aff_sub5=payload.aff_sub5 or "v2.0",
        conversion_id=payload.conversion_id,
        order_id=payload.order_id,
        merchant=merchant_name,
        commission=commission,
        cashback=cashback,
        status=new_status
    )
    saved_txn = cashback_repo.create(txn)

    # Link record update
    affiliate_link.conversion_id = payload.conversion_id
    affiliate_link.order_id = payload.order_id
    affiliate_link.status = new_status
    if new_status == "approved":
        affiliate_link.approved_commission = commission
        affiliate_link.cashback_amount = cashback
    else:
        affiliate_link.estimated_commission = commission
        affiliate_link.cashback_amount = cashback

    # Add ledger transaction & notification for initial creation
    if new_status == "pending":
        wallet_repo.add_ledger_entry(WalletTransaction(
            user_id=user.id,
            type="cashback_pending",
            amount=cashback,
            reference=f"Pending cashback for conversion {payload.conversion_id}",
            conversion_id=payload.conversion_id,
            tracking_id=tracking_id
        ))
        create_user_notification(
            db, user.id, "purchase_tracked",
            "🛍️ Purchase Tracked!",
            f"Your {merchant_name} purchase was tracked! Pending Cashback: ₱{cashback}."
        )
    elif new_status == "approved":
        wallet_repo.add_ledger_entry(WalletTransaction(
            user_id=user.id,
            type="cashback_approved",
            amount=cashback,
            reference=f"Approved cashback for conversion {payload.conversion_id}",
            conversion_id=payload.conversion_id,
            tracking_id=tracking_id
        ))
        create_user_notification(
            db, user.id, "cashback_approved",
            "🎉 Cashback Approved!",
            f"Your ₱{cashback} cashback from {merchant_name} is now available in your wallet!"
        )

    db.commit()

    # Sync summary fields directly from Ledger SUM
    wallet_repo.sync_user_wallet_with_ledger(user)

    logger.info(
        f"Processed new conversion {payload.conversion_id}. "
        f"User ID={user.id} Wallet: Available=PHP {user.wallet_balance}, Pending=PHP {user.wallet_pending}, Paid=PHP {user.wallet_paid}"
    )
    return saved_txn
