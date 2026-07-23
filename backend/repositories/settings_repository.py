from sqlalchemy.orm import Session
from typing import Optional, List
from decimal import Decimal
from backend.models import CashbackSetting

class SettingsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_merchant_setting(self, merchant_name: Optional[str]) -> Optional[CashbackSetting]:
        """Finds active merchant setting matching merchant name (case-insensitive) or 'Default'."""
        if not merchant_name:
            return self._get_default_setting()

        setting = self.db.query(CashbackSetting).filter(
            CashbackSetting.active == True,
            CashbackSetting.merchant.ilike(f"%{merchant_name}%")
        ).first()

        if not setting:
            return self._get_default_setting()
        return setting

    def _get_default_setting(self) -> Optional[CashbackSetting]:
        return self.db.query(CashbackSetting).filter(
            CashbackSetting.active == True,
            CashbackSetting.merchant.ilike("default")
        ).first()

    def get_cashback_rate(self, merchant_name: Optional[str]) -> Decimal:
        """Returns merchant cashback percentage as a decimal fraction (e.g. 20.00 -> 0.20)."""
        setting = self.get_merchant_setting(merchant_name)
        if setting:
            return Decimal(str(setting.cashback_percentage)) / Decimal("100.00")
        return Decimal("0.20") # 20% default user cashback (80% admin profit)

    def get_cashback_percentage_val(self, merchant_name: Optional[str]) -> Decimal:
        """Returns merchant cashback percentage as a number (e.g. 20.00)."""
        setting = self.get_merchant_setting(merchant_name)
        if setting:
            return setting.cashback_percentage
        return Decimal("20.00")

    def get_all(self) -> List[CashbackSetting]:
        return self.db.query(CashbackSetting).all()

    def create_or_update(self, merchant: str, percentage: Decimal, active: bool = True) -> CashbackSetting:
        setting = self.db.query(CashbackSetting).filter(CashbackSetting.merchant == merchant).first()
        if setting:
            setting.cashback_percentage = percentage
            setting.active = active
        else:
            setting = CashbackSetting(merchant=merchant, cashback_percentage=percentage, active=active)
            self.db.add(setting)
        self.db.commit()
        self.db.refresh(setting)
        return setting
