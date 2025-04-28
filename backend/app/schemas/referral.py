from pydantic import BaseModel
from datetime import datetime

class ReferralCreate(BaseModel):
    inviter_id: str
    user_id: str

class ReferralResponse(BaseModel):
    id: int
    user_id: int
    referrer_id: int
    created_at: datetime
    
    class Config:
        orm_mode = True
