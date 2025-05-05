from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
from datetime import datetime, timezone
from passlib.hash import bcrypt

from app.core.logging import logger
from app.core.security import get_api_key
from app.db.session import get_db
from app.db.models import AdminAuth, User, Device, Subscription
from app.schemas.admin import AdminPasswordCreate, AdminPasswordCheck

router = APIRouter()

@router.get("/has_password")
async def has_password(
    admin_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    admin = db.query(AdminAuth).filter_by(admin_id=admin_id).first()
    return {"has_password": bool(admin)}

@router.post("/set_password", status_code=status.HTTP_200_OK)
async def set_admin_password(
    data: AdminPasswordCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Setting password for admin_id={data.admin_id}")
    
    # Check if password already exists
    existing = db.query(AdminAuth).filter_by(admin_id=data.admin_id).first()
    if existing:
        logger.error(f"Password already exists for admin_id={data.admin_id}")
        raise HTTPException(status_code=400, detail="Password exists")
    
    # Hash the password
    password_hash = bcrypt.hash(data.password)
    
    # Create AdminAuth record
    result = AdminAuth(admin_id=data.admin_id, password_hash=password_hash)
    
    db.add(result)
    db.commit()
    
    logger.info(f"Password set successfully for admin_id={data.admin_id}")
    return {"status": "ok"}

@router.post("/check_password", status_code=status.HTTP_200_OK)
async def check_admin_password(
    data: AdminPasswordCheck,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Checking password for admin_id={data.admin_id}")
    
    # Check admin credentials
    admin = db.query(AdminAuth).filter(AdminAuth.admin_id == data.admin_id).first()
    if not admin or not bcrypt.verify(data.password, admin.password_hash):
        logger.error(f"Incorrect password for admin_id={data.admin_id}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    
    logger.info(f"Password verified successfully for admin_id={data.admin_id}")
    return {"status": "ok"}

@router.get("/users/summary", status_code=status.HTTP_200_OK)
async def get_users_summary(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info("Fetching users summary")
    
    # Total number of users
    total = db.query(User).count()
    
    # Active users (those with at least one active subscription)
    current_time = datetime.now(timezone.utc)
    active = db.query(User).join(Subscription).filter(
        Subscription.end_date > current_time,
        Subscription.is_active == True
    ).distinct(User.user_id).count()
    
    logger.info(f"Users summary: total={total}, active={active}")
    return {"total": total, "active": active}

@router.get("/users", status_code=status.HTTP_200_OK)
async def get_users(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Fetching users: skip={skip}, limit={limit}")
    
    # Fetch users
    users = db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    
    # Prepare response
    current_time = datetime.now(timezone.utc)
    result = []
    for user in users:
        # Fetch active subscriptions
        subscriptions = db.query(Subscription).filter(
            Subscription.user_id == user.user_id,
            Subscription.end_date > current_time,
            Subscription.is_active == True
        ).all()
        
        # Fetch devices
        devices = db.query(Device).filter(Device.user_id == user.user_id).all()
        
        # Form subscription data
        subscription = {
            "device": {"duration": 0, "devices": []},
            "router": {"duration": 0, "devices": []},
            "combo": {"duration": 0, "devices": [], "type": 0}
            }
        
        for sub in subscriptions:
            if sub.type == "device":
                subscription["device"]["duration"] = (sub.end_date - current_time).days
            elif sub.type == "router":
                subscription["router"]["duration"] = (sub.end_date - current_time).days
            elif sub.type == "combo":
                subscription["combo"]["duration"] = (sub.end_date - current_time).days
                subscription["combo"]["type"] = sub.combo_size
        
        for device in devices:
            if device.device == "device":
                subscription["device"]["devices"].append(device.device_name)
            elif device.device == "router":
                subscription["router"]["devices"].append(device.device_name)
            elif device.device == "combo":
                subscription["combo"]["devices"].append(device.device_name)
        
        result.append({
            "user_id": user.user_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "subscription": subscription
        })
    
    logger.info(f"Returning {len(result)} users")
    return result
