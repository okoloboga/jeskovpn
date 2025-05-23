import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
from pydantic import EmailStr

from app.core.logging import logger
from app.core.security import get_api_key
from app.db.session import get_db
from app.db.models import User
from app.schemas.user import UserCreate, UserResponse, UserContact, UserContactUpdate

router = APIRouter()

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
) -> Any:
    # logger.info(f"Getting user with ID: {user_id}")
    
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        logger.error(f"User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.post("/contact", status_code=status.HTTP_200_OK)
async def update_contact(
        data: UserContactUpdate,
        db: Session = Depends(get_db),
        api_key: str = Depends(get_api_key)
) -> dict:
    # logger.info(f"Updating user contact for ID: {data.user_id}; contact_type: {data.contact_type}")

    user = db.query(User).filter(User.user_id == data.user_id).first()

    if not user:
        logger.error(f"User with ID {data.user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    contact_type = data.contact_type.lower()
    contact_value = data.contact.strip()

    if contact_type == 'email':
        EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(EMAIL_REGEX, contact_value):
            logger.info(f"Invalid email format: {contact_value}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )                
            
        user.email_address = contact_value
    elif contact_type == 'phone':
        # Нормализация: удаляем пробелы, тире, скобки, знак "+"
        normalized_phone = re.sub(r'[\s\-\(\)+]', '', contact_value)
        # Валидация: только цифры, 11 цифр, начинается с 7
        if not (normalized_phone.isdigit() and len(normalized_phone) == 11 and normalized_phone.startswith('7')):
            logger.error(f"Invalid phone number format: {contact_value} (normalized: {normalized_phone})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number must be in E.164 format for Russia (e.g., 79000000000)"
            )
        user.phone_number = normalized_phone
        # logger.info(f"Normalized phone number saved: {normalized_phone}")
    else:
        logger.error(f"Invalid contact_type: {data.contact_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid contact_type. Must be 'email' or 'phone'"
        )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "user_id": user.user_id,
        "email_address": user.email_address,
        "phone_number": user.phone_number
    }

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
) -> Any:
    # logger.info(f"Creating user with ID: {user.user_id}")
    
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
        balance=100.0,
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"User with ID {user.user_id} created successfully")
    return {"status": "User created"}
