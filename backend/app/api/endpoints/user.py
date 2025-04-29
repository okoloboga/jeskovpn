from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.core.logging import logger
from app.core.security import get_api_key
from app.db.session import get_db
from app.db.models import User
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
) -> Any:
    logger.info(f"Getting user with ID: {user_id}")
    
    user = db.query(User).filter(User.user_id == user_id).first()

    logger.info(f"BACKEDN USER SUB: {user.subscription}")
    if not user:
        logger.error(f"User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
) -> Any:
    logger.info(f"Creating user with ID: {user.user_id}")
    
    # Check if user already exists
    db_user = db.query(User).filter(User.user_id == user.user_id).first()
    if db_user:
        logger.error(f"User with ID {user.user_id} already exists")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    
    # Create new user
    db_user = User(
        user_id=user.user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        balance=1000.0,
        subscription={
            "device": {"devices": [], "duration": 0},
            "router": {"devices": [], "duration": 0},
            "combo": {"devices": [], "duration": 0, "type": 0}
        }
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"User with ID {user.user_id} created successfully")
    return {"status": "User created"}
