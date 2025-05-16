from pydantic import BaseModel

class AdminPasswordCreate(BaseModel):
    admin_id: int
    password: str

class AdminPasswordCheck(BaseModel):
    admin_id: int
    password: str

class AdminCreate(BaseModel):
    user_id: int
