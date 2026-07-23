from pydantic import BaseModel, Field, ConfigDict, field_serializer
from typing import Optional, List, Generic, TypeVar
from datetime import datetime, timezone
from decimal import Decimal

def ensure_utc_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

# --- Common / Pagination Schemas ---
T = TypeVar('T')

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    total_pages: int

# --- Auth Schemas ---
class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    uuid: str
    name: str
    email: str
    role: str
    wallet_balance: Decimal
    wallet_pending: Decimal
    wallet_paid: Decimal
    estimated_cashback: Optional[Decimal] = Decimal("0.00")
    is_active: bool
    is_flagged: bool
    created_at: datetime

    @field_serializer('created_at', check_fields=False)
    def serialize_created_at(self, dt: datetime, _info):
        return ensure_utc_iso(dt)

    model_config = ConfigDict(from_attributes=True)

# --- Affiliate Schemas ---
class GenerateLinkRequest(BaseModel):
    product_url: str
    offer_id: Optional[int] = None

class DeeplinkResponse(BaseModel):
    success: bool
    deeplink: str
    tracking_id: str
    merchant: Optional[str] = None
    cashback_rate: Optional[str] = None
    estimated_info: Optional[str] = None
    aff_sub1: Optional[str] = None
    aff_sub2: Optional[str] = None
    message: Optional[str] = None

class AffiliateLinkResponse(BaseModel):
    id: int
    user_id: int
    user_name: Optional[str] = None
    tracking_id: str
    aff_sub1: Optional[str] = None
    aff_sub2: Optional[str] = None
    aff_sub3: Optional[str] = None
    aff_sub4: Optional[str] = None
    aff_sub5: Optional[str] = None
    offer_id: int
    original_url: str
    deeplink: str
    status: str
    clicks: int
    conversion_id: Optional[str] = None
    order_id: Optional[str] = None
    estimated_commission: Decimal
    approved_commission: Decimal
    cashback_amount: Decimal
    created_at: datetime

    @field_serializer('created_at', check_fields=False)
    def serialize_created_at(self, dt: datetime, _info):
        return ensure_utc_iso(dt)

    model_config = ConfigDict(from_attributes=True)

# --- Cashback Settings Schema ---
class CashbackSettingSchema(BaseModel):
    id: int
    merchant: str
    cashback_percentage: Decimal
    effective_date: datetime
    active: bool

    model_config = ConfigDict(from_attributes=True)

class CashbackSettingCreate(BaseModel):
    merchant: str
    cashback_percentage: Decimal = Field(gt=0, le=100)
    active: bool = True

# --- Wallet & Withdrawal Schemas ---
class WalletResponse(BaseModel):
    available_balance: Decimal
    pending_cashback: Decimal
    total_paid: Decimal
    estimated_cashback: Optional[Decimal] = Decimal("0.00")

class WalletTransactionResponse(BaseModel):
    id: int
    type: str
    amount: Decimal
    reference: Optional[str] = None
    conversion_id: Optional[str] = None
    tracking_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CreateWithdrawalRequest(BaseModel):
    amount: Decimal = Field(gt=0, description="Amount to withdraw")
    bank_account: Optional[str] = Field(default=None, description="Bank / e-wallet account details")
    payment_method: str = Field(default="Bank Transfer", description="Payment method")

class WithdrawalRequestResponse(BaseModel):
    id: int
    user_id: int
    amount: Decimal
    status: str
    bank_account: Optional[str] = None
    payment_method: str
    reference: Optional[str] = None
    requested_at: datetime
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class ApproveWithdrawalRequest(BaseModel):
    withdrawal_id: int
    reference: Optional[str] = None

class RejectWithdrawalRequest(BaseModel):
    withdrawal_id: int
    reason: Optional[str] = None

# --- Conversion Callback Schemas ---
class ConversionCallbackPayload(BaseModel):
    conversion_id: str
    order_id: Optional[str] = None
    status: str # pending, approved, rejected, cancelled, paid
    commission: Decimal
    merchant: Optional[str] = None
    aff_sub1: Optional[str] = None # tracking_id
    tracking_id: Optional[str] = None # fallback
    aff_sub2: Optional[str] = None # user_id
    aff_sub3: Optional[str] = None
    aff_sub4: Optional[str] = None
    aff_sub5: Optional[str] = None

    def get_tracking_id(self) -> str:
        return self.aff_sub1 or self.tracking_id or ""

class CashbackTransactionResponse(BaseModel):
    id: int
    user_id: int
    tracking_id: str
    aff_sub1: Optional[str] = None
    aff_sub2: Optional[str] = None
    conversion_id: str
    order_id: Optional[str] = None
    merchant: Optional[str] = None
    commission: Decimal
    cashback: Decimal
    admin_profit: Optional[Decimal] = Decimal("0.00")
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Fraud Log Schema ---
class FraudLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    event_type: str
    description: str
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
