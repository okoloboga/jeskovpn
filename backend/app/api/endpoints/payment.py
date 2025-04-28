from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.core.logging import logger
from app.core.security import get_api_key
from app.db.session import get_db
from app.db.models import User, Payment
from app.schemas.payment import BalancePaymentCreate

router = APIRouter()

@router.post("/balance", status_code=status.HTTP_200_OK)
async def process_balance_payment(
    payment: BalancePaymentCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
) -> Any:
    logger.info(f"Processing balance payment: user_id={payment.user_id}, amount={payment.amount}, device_type={payment.device_type}")
    
    # Check if user exists
    user = db.query(User).filter(User.user_id == payment.user_id).first()
    if not user:
        logger.error(f"User with ID {payment.user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user has sufficient balance
    if user.balance < payment.amount:
        logger.error(f"Insufficient balance for user {payment.user_id}: {user.balance} < {payment.amount}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    # Deduct amount from user's balance
    user.balance -= payment.amount
    
    # Create payment record
    db_payment = Payment(
        user_id=payment.user_id,
        amount=payment.amount,
        period=payment.period,
        device_type=payment.device_type,
        payment_type=payment.payment_type,
        status="succeeded"
    )
    
    db.add(db_payment)
    db.commit()
    
    # Update user's subscription
    subscription = user.subscription
    
    if payment.device_type == "device":
        subscription["device"]["duration"] += payment.period
    elif payment.device_type == "router":
        subscription["router"]["duration"] += payment.period
    elif payment.device_type == "combo":
        subscription["combo"]["duration"] += payment.period
    
    user.subscription = subscription
    db.commit()
    
    logger.info(f"Balance payment processed successfully: user_id={payment.user_id}, amount={payment.amount}")
    return {"status": "Payment successful"}
