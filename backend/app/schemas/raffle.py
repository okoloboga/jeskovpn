from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class RaffleCreate(BaseModel):
    type: str
    name: str
    ticket_price: Optional[float] = None
    start_date: datetime
    end_date: datetime
    images: List[str] = []
    is_active: bool = True

class RaffleUpdate(BaseModel):
    name: Optional[str] = None
    ticket_price: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    images: Optional[List[str]] = None
    is_active: Optional[bool] = None

class RaffleResponse(BaseModel):
    id: int
    type: str
    name: str
    ticket_price: Optional[float] = None
    start_date: datetime
    end_date: datetime
    images: List[str] = []
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TicketCreate(BaseModel):
    user_id: int
    count: int

class TicketResponse(BaseModel):
    raffle_id: int
    user_id: int
    count: int

    class Config:
        from_attributes = True

class WinnerCreate(BaseModel):
    user_id: int

class WinnerResponse(BaseModel):
    raffle_id: int
    user_id: int

    class Config:
        from_attributes = True
