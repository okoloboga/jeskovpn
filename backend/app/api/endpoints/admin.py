from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
from passlib.hash import bcrypt

from app.core.logging import logger
from app.core.security import get_api_key
from app.db.session import get_db
from app.db.models import AdminAuth, User

router = APIRouter()

@router.get("/admin/has_password")
async def has_password(
    admin_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    admin = db.query(AdminAuth).filter_by(admin_id=admin_id).first()
    return {"has_password": bool(admin)}

@router.post("/admin/set_password")
async def set_admin_password(
        admin_id: int, 
        password: str, 
        db: Session = Depends(get_db),
        api_key: str = Depends(get_api_key)
):
    existing = db.query(AdminAuth).filter_by(admin_id=admin_id).first()

    if existing:
        raise HTTPException(status_code=400, detail="Password exists")
    password_hash = bcrypt.hash(password)

    db.add(AdminAuth(admin_id=admin_id, password_hash=password_hash))
    db.commit()

    return {"status": "ok"}

@router.post("/admin/check_password")
async def check_admin_password(
        admin_id: int, 
        password: str, 
        db: Session = Depends(get_db),
        api_key: str = Depends(get_api_key)
):
    admin = db.query(AdminAuth).filter_by(admin_id=admin_id).first()

    if not admin or not bcrypt.verify(password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    return {"status": "ok"}

@router.get("/admin/users/summary")
async def get_users_summary(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    total = db.query(User).count()
    active = db.query(User).filter(
        (User.subscription["device"]["duration"].as_integer() > 0) |
        (User.subscription["router"]["duration"].as_integer() > 0) |
        (User.subscription["combo"]["duration"].as_integer() > 0)
    ).count()
    return {"total": total, "active": active}

@router.get("/admin/users")
async def get_users(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    users = db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "user_id": u.user_id,
            "username": u.username,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "subscription": u.subscription
        }
        for u in users
    ]


