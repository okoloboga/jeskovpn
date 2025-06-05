from pydantic import BaseModel, HttpUrl, Field

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

class OutlineServerCreate(BaseModel):
    api_url: HttpUrl
    cert_sha256: str = Field(..., pattern=r"^[A-F0-9]{64}$")
    key_limit: int = Field(..., gt=0)

class OutlineServerResponse(BaseModel):
    id: int
    api_url: str
    cert_sha256: str
    key_count: int
    key_limit: int
    is_active: bool
    created_at: str

class OutlineServerUpdate(BaseModel):
    key_limit: int = Field(..., gt=0)
