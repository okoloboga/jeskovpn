from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional, List

class PaymentBase(BaseModel):
    user_id: int
    amount: float
    period: int
    device_type: str
    device: str
    payment_type: str
    method: str
    
    @validator('amount')
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v

class BalancePaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    id: int
    status: str
    payment_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True

class SubscriptionResponse(BaseModel):
    type: str
    combo_size: int
    remaining_days: int
    monthly_price: float
    device_type: List[str]

class InvoiceBase(BaseModel):
    user_id: int
    invoice_id: str
    amount: float
    currency: str
    status: str
    payload: str

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceResponse(InvoiceBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class InvoiceUpdate(BaseModel):
    status: str
