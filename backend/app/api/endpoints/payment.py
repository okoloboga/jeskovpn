import copy
from sys import builtin_module_names

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from app.core.logging import logger
from app.core.security import get_api_key
from app.db.session import get_db
from app.db.models import User, Payment, Invoice
from app.schemas.payment import BalancePaymentCreate, InvoiceResponse, InvoiceCreate, InvoiceUpdate

router = APIRouter()

@router.post("/balance", status_code=status.HTTP_200_OK)
async def process_balance_payment(
    payment: BalancePaymentCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
) -> Any:
    logger.info(f"Processing balance payment: user_id={payment.user_id}, amount={payment.amount}, device_type={payment.device_type},\
                device={payment.device}, payment_type={payment.payment_type}, method={payment.method}")
    
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
      
    # Create payment record
    db_payment = Payment(
        user_id=payment.user_id,
        amount=payment.amount,
        period=payment.period,
        device_type=payment.device_type,
        payment_type=payment.payment_type,
        method=payment.method,
        status="succeeded"
    )
    
    db.add(db_payment)
    
    if payment.method != 'balance':
        user.balance = (user.balance or 0) + payment.amount
    
    # Update user's subscription
    subscription = copy.deepcopy(user.subscription)
    
    if payment.device_type == "device":
        subscription["device"]["duration"] = payment.period
    elif payment.device_type == "router":
        subscription["router"]["duration"] = payment.period
    elif payment.device_type == "combo":
        subscription["combo"]["duration"] = payment.period
        subscription["combo"]["type"] = payment.device
    
    user.subscription = subscription

    logger.info(f'User subscription: {user.subscription}')

    db.commit()
    
    logger.info(f"Balance payment processed successfully: user_id={payment.user_id}, amount={payment.amount}")
    return {"status": "Payment successful"}

@router.post("/invoices/", response_model=InvoiceResponse)
async def create_invoice(
        invoice: InvoiceCreate, 
        db: Session = Depends(get_db),
        api_key: str = Depends(get_api_key)
) -> Any:
    db_invoice = Invoice(**invoice.dict())
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
        invoice_id: str, 
        db: Session = Depends(get_db),
        api_key: str = Depends(get_api_key)
) -> Any:
    db_invoice = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return db_invoice

@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
        invoice_id: str,                 
        invoice_update: InvoiceUpdate,
        db: Session = Depends(get_db),
        api_key: str = Depends(get_api_key)
) -> Any:
    db_invoice = db.query(Invoice).filter(Invoice.invoice_id == invoice_id).first()
    if not db_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    db_invoice.status = invoice_update.status
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

@router.get("/invoices/", response_model=List[InvoiceResponse])
async def get_invoices(
        status: Optional[str] = None, 
        db: Session = Depends(get_db),
        api_key: str = Depends(get_api_key)
        ):
    query = db.query(Invoice)
    if status:
        query = query.filter(Invoice.status == status)
    return query.all()
