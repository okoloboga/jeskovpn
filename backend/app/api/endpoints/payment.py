import copy
from sys import builtin_module_names

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from datetime import datetime, timedelta, timezone

from app.core.logging import logger
from app.core.security import get_api_key
from app.db.session import get_db
from app.db.models import User, Payment, Invoice, Subscription, Device, Raffle, Ticket
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
) -> dict:
    logger.info(f"Processing balance payment: user_id={payment.user_id}, amount={payment.amount}, "
                f"device_type={payment.device_type}, device={payment.device}, "
                f"payment_type={payment.payment_type}, method={payment.method}")
    
    # Проверка существования пользователя
    user = db.query(User).filter(User.user_id == payment.user_id).first()
    if not user:
        logger.error(f"User with ID {payment.user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Обработка add_balance
    if payment.payment_type == "add_balance":
        if payment.amount <= 0:
            logger.error(f"Invalid amount for add_balance: {payment.amount}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be positive for add_balance"
            )
        
        user.balance = (user.balance or 0) + payment.amount
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
    
    # Обработка покупки билетов
    if payment.payment_type == "ticket":
        try:
            raffle_id = int(payment.device)  # device содержит raffle_id
        except ValueError:
            logger.error(f"Invalid raffle_id: {payment.device}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid raffle_id"
            )
        
        raffle = db.query(Raffle).filter(Raffle.id == raffle_id).first()
        if not raffle or not raffle.is_active or raffle.type != "ticket":
            logger.error(f"Invalid or inactive raffle: raffle_id={raffle_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or inactive raffle"
            )
        
        # Проверяем, что сумма соответствует цене билетов
        if raffle.ticket_price is None or raffle.ticket_price <= 0:
            logger.error(f"Invalid ticket price for raffle: raffle_id={raffle_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ticket price"
            )
        
        ticket_count = payment.amount // raffle.ticket_price
        if ticket_count <= 0 or payment.amount % raffle.ticket_price != 0:
            logger.error(f"Invalid amount for tickets: amount={payment.amount}, ticket_price={raffle.ticket_price}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be a multiple of ticket price"
            )
        
        # Начисляем билеты
        try:
            db_ticket = db.query(Ticket).filter(
                Ticket.raffle_id == raffle_id,
                Ticket.user_id == int(payment.user_id)  # Явное приведение к int
            ).first()
            if db_ticket:
                db_ticket.count += ticket_count
            else:
                db_ticket = Ticket(
                    raffle_id=raffle_id,
                    user_id=int(payment.user_id),  # Явное приведение к int
                    count=ticket_count
                )
                db.add(db_ticket)
        except Exception as e:
            logger.error(f"Error creating/updating ticket: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing tickets"
            )
        
        # Создаём запись платежа
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
        
        logger.info(f"Tickets purchased successfully: user_id={payment.user_id}, raffle_id={raffle_id}, count={ticket_count}")
        return {"status": "Payment successful"}
    
    # Валидация цены подписки
    expected_price = 0
    combo_size = 0
    current_time = datetime.now(timezone.utc)

    if payment.device_type == "combo":
        subscription = db.query(Subscription).filter(
            Subscription.user_id == payment.user_id,
            Subscription.type == "combo",
            Subscription.end_date > current_time,
            Subscription.is_active == True
        ).first()
        
        if subscription:
            combo_size = subscription.combo_size
        else:
            last_subscription = db.query(Subscription).filter(
                Subscription.user_id == payment.user_id,
                Subscription.type == "combo"
            ).order_by(Subscription.end_date.desc()).first()
            combo_size = last_subscription.combo_size if last_subscription else 5
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
    
    if payment.method == "balance":
        if user.balance < payment.amount:
            logger.error(f"Insufficient balance for user {payment.user_id}: {user.balance} < {payment.amount}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance"
            )
        user.balance -= payment.amount
    
    # Создание записи платежа
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
    
    # Обновление или создание подписки
    current_time = datetime.now(timezone.utc)
    duration_days = int(payment.period) * 30
    
    if payment.device_type == "combo":
        subscription = db.query(Subscription).filter(
            Subscription.user_id == payment.user_id,
            Subscription.type == "combo",
            Subscription.combo_size == combo_size,
            Subscription.end_date > current_time,
            Subscription.is_active == True
        ).first()
        
        if subscription:
            subscription.end_date += timedelta(days=duration_days)
            subscription.is_active = True
        else:
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
        last_subscription = db.query(Subscription).filter(
            Subscription.user_id == payment.user_id,
            Subscription.type == payment.device_type
        ).order_by(Subscription.end_date.desc()).first()
        
        start_date = current_time
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
    
    # Начисление билетов для активных розыгрышей типа "subscription"
    active_raffles = db.query(Raffle).filter(
        Raffle.type == "subscription",
        Raffle.is_active == True,
        Raffle.start_date <= current_time,
        Raffle.end_date > current_time
    ).all()
    
    ticket_count = int(payment.period) if payment.device_type != "combo" else combo_size + 1
    
    for raffle in active_raffles:
        if current_time >= raffle.start_date:
            ticket = db.query(Ticket).filter(
                Ticket.raffle_id == raffle.id,
                Ticket.user_id == int(payment.user_id)
            ).first()
            if ticket:
                ticket.count += ticket_count
            else:
                ticket = Ticket(
                    raffle_id=raffle.id,
                    user_id=int(payment.user_id),
                    count=ticket_count
                )
                db.add(ticket)
    
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
