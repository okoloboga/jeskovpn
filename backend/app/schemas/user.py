from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# Device subscription schemas
class DeviceSubscription(BaseModel):
    devices: List[str] = []
    duration: int = 0

class RouterSubscription(BaseModel):
    devices: List[str] = []
    duration: int = 0

class ComboSubscription(BaseModel):
    devices: List[str] = []
    duration: int = 0
    type: int = 0

# User schemas
class UserBase(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    username: str

class UserContact(BaseModel):
    user_id: int
    contact_type: str = "any"

    class Config:
        from_attributes = True

class UserContactUpdate(BaseModel):
    user_id: int
    contact_type: str
    contact: str

class UserCreate(UserBase):
    pass

class UserResponse(BaseModel):
    user_id: int
    balance: float
    email_address: str | None
    phone_number: str | None
    
    class Config:
        orm_mode = True

class UserInDB(UserBase):
    balance: float = 0.0
    created_at: datetime
    
    class Config:
        orm_mode = True
