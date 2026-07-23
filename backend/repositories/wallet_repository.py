from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Tuple, Dict
from decimal import Decimal
from backend.models import WalletTransaction, User

class WalletRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_ledger_entry(self, txn: WalletTransaction) -> WalletTransaction:
        """Adds an immutable ledger transaction entry."""
        self.db.add(txn)
        self.db.commit()
        self.db.refresh(txn)
        return txn

    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 20) -> Tuple[List[WalletTransaction], int]:
        query = self.db.query(WalletTransaction).filter(WalletTransaction.user_id == user_id)
        total = query.count()
        items = query.order_by(WalletTransaction.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def recalculate_wallet_from_ledger(self, user_id: int) -> Dict[str, Decimal]:
        """
        Derives user wallet balances from immutable ledger entries.
        Wallet balance = SUM(cashback_approved + manual_adjustment + refund) - SUM(withdrawal_paid)
        Pending balance = SUM(cashback_pending) - SUM(cashback_approved + cashback_reversed)
        Total paid = SUM(withdrawal_paid)
        """
        txns = self.db.query(WalletTransaction).filter(WalletTransaction.user_id == user_id).all()
        
        pending = Decimal("0.00")
        balance = Decimal("0.00")
        paid = Decimal("0.00")

        for t in txns:
            amt = Decimal(str(t.amount))
            if t.type == "cashback_pending":
                pending += amt
            elif t.type == "cashback_approved":
                pending = max(Decimal("0.00"), pending - amt)
                balance += amt
            elif t.type == "cashback_reversed":
                pending = max(Decimal("0.00"), pending - amt)
            elif t.type == "withdrawal_paid":
                balance = max(Decimal("0.00"), balance - amt)
                paid += amt
            elif t.type in ["manual_adjustment", "refund"]:
                balance += amt

        return {
            "wallet_balance": balance,
            "wallet_pending": pending,
            "wallet_paid": paid
        }

    def sync_user_wallet_with_ledger(self, user: User):
        """Updates user summary balance fields from Derived Ledger Sum."""
        ledger_summary = self.recalculate_wallet_from_ledger(user.id)
        user.wallet_balance = ledger_summary["wallet_balance"]
        user.wallet_pending = ledger_summary["wallet_pending"]
        user.wallet_paid = ledger_summary["wallet_paid"]
        self.db.commit()
        self.db.refresh(user)
