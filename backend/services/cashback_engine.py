from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ICashbackStrategy(ABC):
    """Abstract Strategy interface for calculating user cashback."""
    
    @abstractmethod
    def calculate(self, commission: Decimal, order_amount: Optional[Decimal] = None) -> Decimal:
        """Calculates exact user cashback based on commission and optional order amount."""
        pass

class PercentageStrategy(ICashbackStrategy):
    """Calculates cashback as a percentage of reported affiliate commission."""
    
    def __init__(self, percentage: Decimal):
        self.percentage = Decimal(str(percentage))

    def calculate(self, commission: Decimal, order_amount: Optional[Decimal] = None) -> Decimal:
        if commission <= Decimal("0.00"):
            return Decimal("0.00")
        rate = self.percentage / Decimal("100.00")
        cashback = (commission * rate).quantize(Decimal("0.01"))
        return max(Decimal("0.00"), cashback)

class FixedStrategy(ICashbackStrategy):
    """Calculates cashback as a fixed monetary amount per conversion."""
    
    def __init__(self, fixed_amount: Decimal):
        self.fixed_amount = Decimal(str(fixed_amount))

    def calculate(self, commission: Decimal, order_amount: Optional[Decimal] = None) -> Decimal:
        if commission <= Decimal("0.00"):
            return Decimal("0.00")
        # Ensure fixed cashback does not exceed total commission
        return min(self.fixed_amount, commission).quantize(Decimal("0.01"))

class TieredStrategy(ICashbackStrategy):
    """
    Calculates cashback based on tiered commission thresholds.
    Example tier_config:
    [
        {"max": 50, "percentage": 50},
        {"min": 50, "max": 200, "percentage": 70},
        {"min": 200, "percentage": 85}
    ]
    """
    
    def __init__(self, tier_config: List[Dict[str, Any]]):
        self.tier_config = tier_config or []

    def calculate(self, commission: Decimal, order_amount: Optional[Decimal] = None) -> Decimal:
        if commission <= Decimal("0.00"):
            return Decimal("0.00")
            
        applicable_percentage = Decimal("20.00") # Default fallback
        
        for tier in self.tier_config:
            min_val = Decimal(str(tier.get("min", 0)))
            max_val = Decimal(str(tier.get("max", "999999999"))) if tier.get("max") is not None else Decimal("999999999")
            
            if min_val <= commission <= max_val:
                applicable_percentage = Decimal(str(tier.get("percentage", 20)))
                break

        rate = applicable_percentage / Decimal("100.00")
        cashback = (commission * rate).quantize(Decimal("0.01"))
        return max(Decimal("0.00"), cashback)

class CashbackPolicyEngine:
    """Context runner selecting and executing the active cashback strategy."""
    
    @staticmethod
    def get_strategy(policy_type: str, policy_value: Decimal, tier_config: Optional[List[Dict[str, Any]]] = None) -> ICashbackStrategy:
        ptype = (policy_type or "percentage").lower()
        if ptype == "fixed":
            return FixedStrategy(fixed_amount=policy_value)
        elif ptype == "tiered" and tier_config:
            return TieredStrategy(tier_config=tier_config)
        else:
            return PercentageStrategy(percentage=policy_value)

    @classmethod
    def calculate_cashback(
        cls,
        commission: Decimal,
        policy_type: str = "percentage",
        policy_value: Decimal = Decimal("20.00"),
        min_cashback: Optional[Decimal] = None,
        max_cashback: Optional[Decimal] = None,
        tier_config: Optional[List[Dict[str, Any]]] = None,
        order_amount: Optional[Decimal] = None
    ) -> Decimal:
        strategy = cls.get_strategy(policy_type, policy_value, tier_config)
        raw_cashback = strategy.calculate(commission, order_amount)
        
        # Enforce minimum / maximum caps if specified
        if min_cashback is not None and min_cashback > Decimal("0.00") and raw_cashback < min_cashback:
            raw_cashback = min_cashback
        if max_cashback is not None and max_cashback > Decimal("0.00") and raw_cashback > max_cashback:
            raw_cashback = max_cashback
            
        return raw_cashback.quantize(Decimal("0.01"))
