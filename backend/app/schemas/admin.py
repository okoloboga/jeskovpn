from pydantic import BaseModel

class AdminPasswordCreate(BaseModel):
    admin_id: int
    password: str

class AdminPasswordCheck(BaseModel):
    admin_id: int
    password: str

class AdminCreate(BaseModel):
    user_id: int

class PromocodeCreate(BaseModel):
    code: str
    type: str
    max_usage: int

class PromocodeUsageCreate(BaseModel):
    user_id: int
    promocode_code: str
