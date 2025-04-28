from pydantic import BaseModel, validator
from datetime import datetime
from typing import Optional

class PaymentBase(BaseModel):
    user_id: int
    amount: float
    period: int
    device_type: str
    payment_type: str
    
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
