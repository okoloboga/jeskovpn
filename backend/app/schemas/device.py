from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class DeviceKeyCreate(BaseModel):
    user_id: int
    device: str
    device_name: str
    slot: str

class DeviceKeyGet(BaseModel):
    user_id: int
    device_name: str

class DeviceKeyPut(BaseModel):
    user_id: int
    device_old_name: str
    device_new_name: str

class DeviceKeyDelete(BaseModel):
    user_id: int
    device_name: str

class DeviceUsersResponse(BaseModel):
    device: str
    device_name: str
    device_type: str

class UserDevicesResponse(BaseModel):
    device: List[DeviceUsersResponse]
    router: List[DeviceUsersResponse]
    combo: List[DeviceUsersResponse]

class DeviceResponse(BaseModel):
    id: int
    user_id: int
    device_name: str
    vpn_key: str
    outline_key_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        orm_mode = True
