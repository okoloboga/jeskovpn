from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DeviceKeyCreate(BaseModel):
    user_id: int
    device: str
    slot: str

class DeviceKeyGet(BaseModel):
    user_id: int
    device: str

class DeviceKeyDelete(BaseModel):
    user_id: int
    device: str

class DeviceResponse(BaseModel):
    id: int
    user_id: int
    device_name: str
    vpn_key: str
    outline_key_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True
