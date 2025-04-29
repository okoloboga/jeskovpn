from sqlalchemy import Column, BigInteger, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from .base import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(BigInteger, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    subscription = Column(JSON, default={
        "device": {"devices": [], "duration": 0},
        "router": {"devices": [], "duration": 0},
        "combo": {"devices": [], "duration": 0, "type": 0}
    })

class Referral(Base):
    __tablename__ = "referrals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    referrer_id = Column(Integer, ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    amount = Column(Float)
    period = Column(Integer)
    device_type = Column(String)
    payment_type = Column(String)
    status = Column(String, default="pending")
    payment_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    device_name = Column(String)
    vpn_key = Column(String)
    outline_key_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
