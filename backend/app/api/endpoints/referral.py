from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.core.logging import logger
from app.core.security import get_api_key
from app.db.session import get_db
from app.db.models import User, Referral
from app.schemas.referral import ReferralCreate

router = APIRouter()

@router.post("", status_code=status.HTTP_200_OK)
async def add_referral(
    referral: ReferralCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
) -> Any:
    try:
        user_id = int(referral.user_id)
        referrer_id = int(referral.inviter_id)
    except ValueError:
        logger.error("Invalid user_id or inviter_id format")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user_id or inviter_id format"
        )
    
    # logger.info(f"Adding referral: user_id={user_id}, referrer_id={referrer_id}")
    
    # Check if user exists
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        logger.error(f"User with ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if referrer exists
    referrer = db.query(User).filter(User.user_id == referrer_id).first()
    if not referrer:
        logger.error(f"Referrer with ID {referrer_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referrer not found"
        )
    
    # Create new referral
    db_referral = Referral(
        user_id=user_id,
        referrer_id=referrer_id
    )
    
    db.add(db_referral)
    db.commit()
    
    logger.info(f"Referral added successfully: user_id={user_id}, referrer_id={referrer_id}")
    return {"status": "Referral added"}
