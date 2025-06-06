from sqlalchemy import Column, BigInteger, Boolean, Integer, String, Float, \
        DateTime, ForeignKey, JSON, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(BigInteger, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    username = Column(String)
    balance = Column(Float, default=0.0)
    email_address = Column(String)
    phone_number = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Referral(Base):
    __tablename__ = "referrals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    referrer_id = Column(BigInteger, ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(BigInteger, index=True)
    invoice_id = Column(String, unique=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    payload = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    amount = Column(Float)
    period = Column(Integer)    
    device_type = Column(String)
    device = Column(String)
    payment_type = Column(String)
    method = Column(String)
    status = Column(String, default="pending")
    payment_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), index=True)
    type = Column(String, nullable=False)  # device, router, combo
    combo_size = Column(Integer, default=0)  # 0 for device/router, 5/10 for combo
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    paused_at = Column(DateTime(timezone=True), nullable=True)
    
    __table_args__ = (
        {"comment": "Stores user subscriptions with start and end dates"},
    )

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"))
    device = Column(String)  # SLOT: Device / Router / Combo
    device_type = Column(String)  # Device / Router
    device_name = Column(String)
    vpn_key = Column(String)
    outline_key_id = Column(String, nullable=True)
    server_id = Column(Integer, ForeignKey("outline_servers.id", ondelete="SET NULL"))
    start_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class OutlineServer(Base):
    __tablename__ = "outline_servers"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    api_url = Column(String(255), nullable=False)
    cert_sha256 = Column(String(64), nullable=False)
    key_count = Column(Integer, default=0)
    key_limit = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class AdminAuth(Base):
    __tablename__ = "admin_auth"

    admin_id = Column(BigInteger, primary_key=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Blacklist(Base):
    __tablename__ = "blacklist"
    
    user_id = Column(BigInteger, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        {"comment": "Stores blocked user IDs"},
    )

class Admin(Base):
    __tablename__ = "admins"
    
    user_id = Column(BigInteger, primary_key=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        {"comment": "Stores admin user IDs"},
    )

class Promocode(Base):
    __tablename__ = "promocodes"
    code = Column(String(50), primary_key=True)
    type = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    max_usage = Column(Integer, default=0, nullable=False)

class PromocodeUsage(Base):
    __tablename__ = "promocode_usages"
    user_id = Column(BigInteger, ForeignKey("users.user_id"), primary_key=True)
    promocode_code = Column(String(50), ForeignKey("promocodes.code", ondelete="CASCADE"), primary_key=True)
    used_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class Raffle(Base):
    __tablename__ = "raffles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String, nullable=False)  # "subscription" or "ticket"
    name = Column(String, nullable=False)  # Название розыгрыша
    ticket_price = Column(Float, nullable=True)  # Цена билета для типа "ticket" (например, 100.0)
    start_date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    images = Column(ARRAY(String), nullable=True)  # Список file_id картинок из Telegram
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tickets = relationship("Ticket", back_populates="raffle")
    winners = relationship("Winner", back_populates="raffle")
    
    __table_args__ = (
        {"comment": "Stores raffle details"},
    )

class Ticket(Base):
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    raffle_id = Column(Integer, ForeignKey("raffles.id"), index=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), index=True)
    count = Column(Integer, default=0)  # Количество билетов
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    raffle = relationship("Raffle", back_populates="tickets")
    user = relationship("User")
    
    __table_args__ = (
        {"comment": "Stores user tickets for raffles"},
    )


class Winner(Base):
    __tablename__ = "winners"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    raffle_id = Column(Integer, ForeignKey("raffles.id"), index=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    raffle = relationship("Raffle", back_populates="winners")
    user = relationship("User")
    
    __table_args__ = (
        {"comment": "Stores raffle winners"},
    )

