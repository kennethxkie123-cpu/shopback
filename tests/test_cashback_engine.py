import pytest
from decimal import Decimal
from backend.services.cashback_engine import (
    CashbackPolicyEngine,
    PercentageStrategy,
    FixedStrategy,
    TieredStrategy
)

def test_percentage_strategy():
    strategy = PercentageStrategy(percentage=Decimal("20.00"))
    
    # 20% of 100 commission = 20
    assert strategy.calculate(Decimal("100.00")) == Decimal("20.00")
    # 20% of 50 commission = 10
    assert strategy.calculate(Decimal("50.00")) == Decimal("10.00")
    # 0 commission = 0
    assert strategy.calculate(Decimal("0.00")) == Decimal("0.00")

def test_fixed_strategy():
    strategy = FixedStrategy(fixed_amount=Decimal("15.00"))
    
    # Commission 50 > Fixed 15 => 15
    assert strategy.calculate(Decimal("50.00")) == Decimal("15.00")
    # Commission 10 < Fixed 15 => capped at commission 10
    assert strategy.calculate(Decimal("10.00")) == Decimal("10.00")

def test_tiered_strategy():
    tier_config = [
        {"max": 50, "percentage": 50},
        {"min": 50, "max": 200, "percentage": 70},
        {"min": 200, "percentage": 85}
    ]
    strategy = TieredStrategy(tier_config=tier_config)
    
    # Commission 30 (< 50) => 50% of 30 = 15.00
    assert strategy.calculate(Decimal("30.00")) == Decimal("15.00")
    # Commission 100 (50-200) => 70% of 100 = 70.00
    assert strategy.calculate(Decimal("100.00")) == Decimal("70.00")
    # Commission 300 (> 200) => 85% of 300 = 255.00
    assert strategy.calculate(Decimal("300.00")) == Decimal("255.00")

def test_cashback_policy_engine_min_max_caps():
    # Percentage 20%, but with min cap of 5.00 and max cap of 25.00
    cb_min = CashbackPolicyEngine.calculate_cashback(
        commission=Decimal("10.00"), # 20% of 10 = 2.00 -> min cap = 5.00
        policy_type="percentage",
        policy_value=Decimal("20.00"),
        min_cashback=Decimal("5.00")
    )
    assert cb_min == Decimal("5.00")

    cb_max = CashbackPolicyEngine.calculate_cashback(
        commission=Decimal("200.00"), # 20% of 200 = 40.00 -> max cap = 25.00
        policy_type="percentage",
        policy_value=Decimal("20.00"),
        max_cashback=Decimal("25.00")
    )
    assert cb_max == Decimal("25.00")
