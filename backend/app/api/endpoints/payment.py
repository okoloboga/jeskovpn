import copy
from sys import builtin_module_names

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from datetime import datetime, timedelta, timezone

from app.core.logging import logger
from app.core.security import get_api_key
from app.db.session import get_db
from app.db.models import User, Payment, Invoice, Subscription, Device
from app.schemas.payment import BalancePaymentCreate, InvoiceResponse, InvoiceCreate, InvoiceUpdate, SubscriptionResponse

router = APIRouter()

MONTH_PRICE = {
    "device": {"0": 0.0, "1": 100.0, "3": 240.0, "6": 420.0, "12": 600.0},
    "router": {"0": 0.0, "1": 250.0, "3": 600.0, "6": 1000.0, "12": 1500.0},
    "combo": {
        "0": {"0": 0.0},
        "5": {"0": 0.0, "1": 500.0, "3": 1200.0, "6": 2100.0, "12": 3000.0},
        "10": {"0": 0.0, "1": 850.0, "3": 2000.0, "6": 3500.0, "12": 5000.0}
    }
}

@router.post("/balance", status_code=status.HTTP_200_OK)
async def process_balance_payment(
    payment: BalancePaymentCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
) -> Any:
    # logger.info(f"Processing balance payment: user_id={payment.user_id}, amount={payment.amount}, device_type={payment.device_type}, "
    #            f"device={payment.device}, payment_type={payment.payment_type}, method={payment.method}")
    
    # Check if user exists
    user = db.query(User).filter(User.user_id == payment.user_id).first()
    if not user:
        logger.error(f"User with ID {payment.user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Handle add_balance case
    if payment.payment_type == "add_balance":
        if payment.amount <= 0:
            logger.error(f"Invalid amount for add_balance: {payment.amount}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be positive for add_balance"
            )
        
        # Add to balance
        user.balance = (user.balance or 0) + payment.amount
        
        # Create payment record
        db_payment = Payment(
            user_id=payment.user_id,
            amount=payment.amount,
            period=payment.period,
            device_type=payment.device_type,
            device=payment.device,
            payment_type=payment.payment_type,
            method=payment.method,
            status="succeeded"
        )
        db.add(db_payment)
        db.commit()
        
        logger.info(f"Balance added successfully: user_id={payment.user_id}, amount={payment.amount}")
        return {"status": "Payment successful"}
    
    # Validate price for subscription
    expected_price = 0
    combo_size = 0
    current_time = datetime.now(timezone.utc)

    if payment.device_type == "combo":
        # Find active combo subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == payment.user_id,
            Subscription.type == "combo",
            Subscription.end_date > current_time,
            Subscription.is_active == True
        ).first()
        
        if subscription:
            combo_size = subscription.combo_size
        else:
            # Find last non-active subscription
            last_subscription = db.query(Subscription).filter(
                Subscription.user_id == payment.user_id,
                Subscription.type == "combo"
            ).order_by(Subscription.end_date.desc()).first()
            combo_size = last_subscription.combo_size if last_subscription else 5  # Default to 5 if no previous subscription
            combo_size = 10 if payment.device == "10" else combo_size
        try:
            expected_price = MONTH_PRICE["combo"][str(combo_size)][str(payment.period)]
        except KeyError:
            logger.error(f"Invalid combo size or period: combo_size={combo_size}, period={payment.period}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid combo size or period"
            )
    else:
        try:
            expected_price = MONTH_PRICE[payment.device_type][str(payment.period)]
        except KeyError:
            logger.error(f"Invalid device type or period: {payment.device_type}, {payment.period}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid device type or period"
            )

    if payment.amount != expected_price and payment.method != 'promo':
        logger.error(f"Amount mismatch: provided={payment.amount}, expected={expected_price}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount does not match expected price"
        )
    
    # Check balance for balance payment
    if payment.method == "balance":
        if user.balance < payment.amount:
            logger.error(f"Insufficient balance for user {payment.user_id}: {user.balance} < {payment.amount}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance"
            )
        user.balance -= payment.amount
    
    # Create payment record
    db_payment = Payment(
        user_id=payment.user_id,
        amount=payment.amount,
        period=payment.period,
        device_type=payment.device_type,
        device=payment.device,
        payment_type=payment.payment_type,
        method=payment.method,
        status="succeeded"
    )
    db.add(db_payment)
    
    # Update or create subscription
    current_time = datetime.now(timezone.utc)
    duration_days = payment.period * 30
    
    if payment.device_type == "combo":
        # For combo, extend existing subscription if it exists
        subscription = db.query(Subscription).filter(
            Subscription.user_id == payment.user_id,
            Subscription.type == "combo",
            Subscription.combo_size == combo_size,
            Subscription.end_date > current_time,
            Subscription.is_active == True
        ).first()
        
        if subscription:
            # Extend existing combo subscription
            subscription.end_date += timedelta(days=duration_days)
            subscription.is_active = True
        else:
            # Create new combo subscription
            last_subscription = db.query(Subscription).filter(
                Subscription.user_id == payment.user_id,
                Subscription.type == "combo",
                Subscription.combo_size == combo_size
            ).order_by(Subscription.end_date.desc()).first()
            
            start_date = current_time
            if last_subscription and last_subscription.end_date > current_time:
                start_date = last_subscription.end_date
            
            subscription = Subscription(
                user_id=payment.user_id,
                type=payment.device_type,
                combo_size=combo_size,
                start_date=start_date,
                end_date=start_date + timedelta(days=duration_days),
                is_active=True
            )
            db.add(subscription)
    else:
        # For device or router, always create a new subscription
        last_subscription = db.query(Subscription).filter(
            Subscription.user_id == payment.user_id,
            Subscription.type == payment.device_type
        ).order_by(Subscription.end_date.desc()).first()
        
        start_date = current_time
        # if last_subscription and last_subscription.end_date > current_time:
        #    start_date = last_subscription.end_date
        
        subscription = Subscription(
            user_id=payment.user_id,
            type=payment.device_type,
            combo_size=0,
            start_date=start_date,
            end_date=start_date + timedelta(days=duration_days),
            is_active=True,
            paused_at=start_date
        )
        db.add(subscription)
    
    # Skip device synchronization until device is created
    # Devices will be synced when added via POST /devices/key
    db.commit()
    
    logger.info(f"Balance payment processed successfully: user_id={payment.user_id}, amount={payment.amount}")
    return {"status": "Payment successful"}

@router.get("/subscriptions/{user_id}", response_model=List[SubscriptionResponse])
async def get_subscriptions(
    user_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    # logger.info(f"Fetching subscriptions for user_id={user_id}")
    
    current_time = datetime.now(timezone.utc)
    subscriptions = db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.end_date > current_time,
        Subscription.is_active == True
    ).all()

    result = []
    for sub in subscriptions:
        # Calculate remaining days
        remaining_days_raw = sub.end_date - current_time
        remaining_days = int(remaining_days_raw.days)

        # Find the latest payment for this subscription
        payment_filter = [
            Payment.user_id == user_id,
            Payment.device_type == sub.type,
            Payment.status == "succeeded"
        ]
        if sub.type == "combo":
            payment_filter.append(Payment.device == str(sub.combo_size))
        
        payment = db.query(Payment).filter(*payment_filter).order_by(Payment.created_at.desc()).first()

        monthly_price = 0.0
        if payment and payment.period > 0:
            monthly_price = payment.amount / payment.period
            logger.info(f"Payment found for sub_id={sub.id}, type={sub.type}, monthly_price={monthly_price}")

        # Fetch associated devices
        devices = db.query(Device).filter(
            Device.user_id == user_id,
            Device.device == sub.type,
            Device.start_date == sub.start_date,
            Device.end_date == sub.end_date
        ).all()
        
        # Extract unique device types
        device_types = list({device.device_type for device in devices if device.device_type})

        result.append({
            "type": sub.type,
            "combo_size": sub.combo_size,
            "remaining_days": remaining_days,
            "monthly_price": round(monthly_price, 2),
            "device_type": device_types,
            "paused_at": sub.paused_at
        })
    
    logger.info(f"Returning {len(result)} active subscriptions for user_id={user_id}")
    return result

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
