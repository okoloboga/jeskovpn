import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import or_, func
from typing import Any, Optional
from datetime import datetime, timezone, timedelta
from passlib.hash import bcrypt

from app.core.logging import logger
from app.core.security import get_api_key
from app.db.session import get_db
from app.db.models import AdminAuth, User, Device, Subscription, Blacklist, Payment, Admin, Promocode, \
        PromocodeUsage, OutlineServer
from app.schemas.admin import AdminPasswordCreate, AdminPasswordCheck, AdminCreate, PromocodeCreate, \
        PromocodeUsageCreate, OutlineServerCreate

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
    user_id: Optional[int] = None,
    query: Optional[str] = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Fetching users: skip={skip}, limit={limit}, user_id={user_id}, query={query}")
    
    # Fetch users
    query_db = db.query(User).order_by(User.created_at.desc())
    if user_id is not None:
        query_db = query_db.filter(User.user_id == user_id)
    elif query is not None:
        # Регистронезависимый поиск по всем полям
        search_term = f"%{query}%"
        query_db = query_db.filter(
            or_(
                func.lower(User.username).like(func.lower(search_term)),
                User.user_id == query if query.isdigit() else False,
                func.lower(User.first_name).like(func.lower(search_term)),
                func.lower(User.last_name).like(func.lower(search_term)),
                func.lower(User.email_address).like(func.lower(search_term)),
                func.lower(User.phone_number).like(func.lower(search_term))
            )
        )
    
    users = query_db.offset(skip).limit(limit).all()
    
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
            "subscription": subscription,
            "email_address": user.email_address,
            "balance": user.balance,
            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M"),
            "is_blacklisted": bool(db.query(Blacklist).filter(Blacklist.user_id == user.user_id).first())
        })
    
    logger.info(f"Returning {len(result)} users")
    return result

@router.post("/users/{user_id}/block")
async def block_user(user_id: int, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    logger.info(f"Blocking user {user_id}")
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        logger.error(f"User {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")
    
    # Добавляем в черный список
    blacklist_entry = db.query(Blacklist).filter(Blacklist.user_id == user_id).first()
    if not blacklist_entry:
        blacklist_entry = Blacklist(user_id=user_id)
        db.add(blacklist_entry)
    
    # Деактивируем подписки
    db.query(Subscription).filter(
        Subscription.user_id == user_id, Subscription.is_active == True
    ).update({"is_active": False})
    
    db.commit()
    logger.info(f"User {user_id} blocked successfully")
    return {"status": "success"}

@router.delete("/blacklist/{user_id}")
async def remove_from_blacklist(
    user_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Removing user {user_id} from blacklist")
    
    blacklisted = db.query(Blacklist).filter(Blacklist.user_id == user_id).first()
    if not blacklisted:
        logger.error(f"User {user_id} not found in blacklist")
        raise HTTPException(status_code=404, detail="User not found in blacklist")
    
    db.delete(blacklisted)
    db.commit()
    
    logger.info(f"User {user_id} removed from blacklist")
    return {"status": "success"}

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db), api_key: str = Depends(get_api_key)):
    logger.info(f"Deleting user {user_id}")
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        logger.error(f"User {user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")
    
    # Удаляем связанные данные
    db.query(Subscription).filter(Subscription.user_id == user_id).delete()
    db.query(Device).filter(Device.user_id == user_id).delete()
    db.query(Blacklist).filter(Blacklist.user_id == user_id).delete()
    db.delete(user)
    
    db.commit()
    logger.info(f"User {user_id} deleted successfully")
    return {"status": "success"}

@router.get("/devices")
async def get_devices(
    skip: int = 0,
    limit: int = 20,
    vpn_key: Optional[str] = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Fetching devices: skip={skip}, limit={limit}, vpn_key={vpn_key}")
    
    query = db.query(Device).order_by(Device.created_at.desc())
    if vpn_key is not None:
        query = query.filter(Device.outline_key_id == vpn_key)
    
    devices = query.offset(skip).limit(limit).all()
    current_time = datetime.now(timezone.utc)
    
    result = []
    for device in devices:
        is_active = device.end_date > current_time
        result.append({
            "vpn_key": device.vpn_key,
            "outline_key_id": device.outline_key_id,
            "user_id": device.user_id,
            "device_type": device.device_type,
            "start_date": device.start_date.strftime("%Y-%m-%d %H:%M"),
            "end_date": device.end_date.strftime("%Y-%m-%d %H:%M"),
            "is_active": is_active
        })
    
    logger.info(f"Returning {len(result)} devices")
    return result

@router.get("/devices/history")
async def get_device_history(
    vpn_key: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Fetching history for vpn_key={vpn_key}")
    
    devices = db.query(Device).filter(Device.outline_key_id == vpn_key).order_by(Device.created_at.desc()).all()
    
    result = [
        {
            "user_id": device.user_id,
            "device_type": device.device_type,
            "device_name": device.device_name,
            "start_date": device.start_date.strftime("%Y-%m-%d %H:%M"),
            "end_date": device.end_date.strftime("%Y-%m-%d %H:%M")
        }
        for device in devices
    ]
    
    logger.info(f"Returning {len(result)} history entries for vpn_key={vpn_key}")
    return result

@router.get("/payments/summary")
async def get_payments_summary(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info("Fetching payments summary")
    
    current_time = datetime.now(timezone.utc)
    day_ago = current_time - timedelta(days=1)
    month_ago = current_time - timedelta(days=30)
    
    # Инициализация результата
    result = {
        "day": {"total_amount": 0.0, "total_count": 0, "by_method": {"ukassa": {"amount": 0.0, "count": 0}, "crypto": {"amount": 0.0, "count": 0}, "stars": {"amount": 0.0, "count": 0}}},
        "month": {"total_amount": 0.0, "total_count": 0, "by_method": {"ukassa": {"amount": 0.0, "count": 0}, "crypto": {"amount": 0.0, "count": 0}, "stars": {"amount": 0.0, "count": 0}}},
        "all_time": {"total_amount": 0.0, "total_count": 0, "by_method": {"ukassa": {"amount": 0.0, "count": 0}, "crypto": {"amount": 0.0, "count": 0}, "stars": {"amount": 0.0, "count": 0}}}
    }
    
    # За день
    day_query = db.query(
        Payment.method,
        func.sum(Payment.amount).label("amount"),
        func.count(Payment.id).label("count")
    ).filter(
        Payment.status == "succeeded",
        Payment.created_at >= day_ago
    ).group_by(Payment.method).all()
    logger.info(f"Day query result: {day_query}")
    
    for method, amount, count in day_query:
        if method in result["day"]["by_method"]:
            result["day"]["by_method"][method] = {"amount": round(float(amount), 2), "count": count}
            result["day"]["total_amount"] += float(amount)
            result["day"]["total_count"] += count
    
    # За месяц
    month_query = db.query(
        Payment.method,
        func.sum(Payment.amount).label("amount"),
        func.count(Payment.id).label("count")
    ).filter(
        Payment.status == "succeeded",
        Payment.created_at >= month_ago
    ).group_by(Payment.method).all()
    logger.info(f"Month query result: {month_query}")
    
    for method, amount, count in month_query:
        if method in result["month"]["by_method"]:
            result["month"]["by_method"][method] = {"amount": round(float(amount), 2), "count": count}
            result["month"]["total_amount"] += float(amount)
            result["month"]["total_count"] += count
    
    # За всё время
    all_time_query = db.query(
        Payment.method,
        func.sum(Payment.amount).label("amount"),
        func.count(Payment.id).label("count")
    ).filter(
        Payment.status == "succeeded"
    ).group_by(Payment.method).all()
    logger.info(f"All time query result: {all_time_query}")
    
    for method, amount, count in all_time_query:
        if method in result["all_time"]["by_method"]:
            result["all_time"]["by_method"][method] = {"amount": round(float(amount), 2), "count": count}
            result["all_time"]["total_amount"] += float(amount)
            result["all_time"]["total_count"] += count
    
    result["day"]["total_amount"] = round(result["day"]["total_amount"], 2)
    result["month"]["total_amount"] = round(result["month"]["total_amount"], 2)
    result["all_time"]["total_amount"] = round(result["all_time"]["total_amount"], 2)
    
    logger.info(f"Payments summary: {result}")
    return result

@router.get("/users/ids")
async def get_all_users(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info("Fetching all user IDs")
    
    user_ids = db.query(User.user_id).all()
    result = [user_id for (user_id,) in user_ids]
    
    logger.info(f"Returning {len(result)} user IDs")
    return result

@router.get("/admins")
async def get_admins(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info("Fetching admins")
    
    admins = db.query(Admin).all()
    result = [
        {
            "user_id": admin.user_id,
            "added_at": admin.added_at.strftime("%Y-%m-%d %H:%M")
        }
        for admin in admins
    ]
    
    logger.info(f"Returning {len(result)} admins")
    return result

@router.post("/admins")
async def add_admin(
    admin: AdminCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Adding admin {admin.user_id}")
    
    existing_admin = db.query(Admin).filter(Admin.user_id == admin.user_id).first()
    if existing_admin:
        logger.error(f"Admin {admin.user_id} already exists")
        raise HTTPException(status_code=400, detail="Admin already exists")
    
    new_admin = Admin(user_id=admin.user_id)
    db.add(new_admin)
    db.commit()
    
    logger.info(f"Admin {admin.user_id} added")
    return {"status": "success"}

@router.delete("/admins/{user_id}")
async def delete_admin(
    user_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Deleting admin {user_id}")
    
    admin = db.query(Admin).filter(Admin.user_id == user_id).first()
    if not admin:
        logger.error(f"Admin {user_id} not found")
        raise HTTPException(status_code=404, detail="Admin not found")
    
    db.delete(admin)
    db.commit()
    
    logger.info(f"Admin {user_id} deleted")
    return {"status": "success"}

@router.get("/admins/check")
async def check_admin(
    user_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Checking if user {user_id} is admin")
    
    admin = db.query(Admin).filter(Admin.user_id == user_id).first()
    is_admin = bool(admin)
    
    logger.info(f"User {user_id} is_admin: {is_admin}")
    return {"is_admin": is_admin}

@router.get("/blacklist/check")
async def check_blacklist(
    user_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Checking if user {user_id} is blacklisted")
    
    blacklisted = db.query(Blacklist).filter(Blacklist.user_id == user_id).first()
    is_blacklisted = bool(blacklisted)
    
    logger.info(f"User {user_id} is_blacklisted: {is_blacklisted}")
    return {"is_blacklisted": is_blacklisted}

@router.get("/promocodes")
async def get_promocodes(
    skip: int = 0,
    limit: int = 20,
    code: Optional[str] = None,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Fetching promocodes: skip={skip}, limit={limit}, code={code}")
    
    query = db.query(Promocode)
    if code is not None:
        query = query.filter(Promocode.code == code)
    
    promocodes = query.offset(skip).limit(limit).all()
    result = []
    for promocode in promocodes:
        usage_count = db.query(PromocodeUsage).filter(
            PromocodeUsage.promocode_code == promocode.code
        ).count()
        result.append({
            "code": promocode.code,
            "type": promocode.type,
            "usage_count": usage_count,
            "max_usage": promocode.max_usage,
            "is_active": promocode.is_active,
            "created_at": promocode.created_at.strftime("%Y-%m-%d %H:%M")
        })
    
    logger.info(f"Returning {len(result)} promocodes")
    return result

@router.post("/promocodes")
async def create_promocode(
    promocode: PromocodeCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Creating promocode: code={promocode.code}, type={promocode.type}, max_usage={promocode.max_usage}")
    
    # Валидация code
    if not re.match(r"^[a-zA-Z0-9]+$", promocode.code):
        logger.error(f"Invalid promocode format: {promocode.code}")
        raise HTTPException(status_code=400, detail="Код должен содержать только буквы и цифры")
    
    # Валидация type
    valid_types = [
        "device_promo", "combo_5", "combo_10",
        *[f"balance_{amount}" for amount in range(1, 10001)]
    ]
    if promocode.type not in valid_types:
        logger.error(f"Invalid promocode type: {promocode.type}")
        raise HTTPException(status_code=400, detail="Недопустимый тип промокода")
    
    # Валидация max_usage
    if promocode.max_usage < 0:
        logger.error(f"Invalid max_usage: {promocode.max_usage}")
        raise HTTPException(status_code=400, detail="Максимальное количество использований должно быть >= 0")
    
    # Проверка уникальности
    if db.query(Promocode).filter(Promocode.code == promocode.code).first():
        logger.error(f"Promocode already exists: {promocode.code}")
        raise HTTPException(
            status_code=400,
            detail=f"Промокод с кодом '{promocode.code}' уже существует"
        )
    
    new_promocode = Promocode(
        code=promocode.code,
        type=promocode.type,
        is_active=True,
        max_usage=promocode.max_usage
    )
    db.add(new_promocode)
    db.commit()
    
    logger.info(f"Promocode created: {promocode.code}")
    return {"status": "success", "code": promocode.code}

@router.post("/promocodes/usage")
async def log_promocode_usage(
    usage: PromocodeUsageCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Logging promocode usage: user_id={usage.user_id}, code={usage.promocode_code}")
    
    promocode = db.query(Promocode).filter(Promocode.code == usage.promocode_code).first()
    if not promocode:
        logger.error(f"Promocode not found: {usage.promocode_code}")
        raise HTTPException(status_code=404, detail="Promocode not found")
    
    if not promocode.is_active:
        logger.error(f"Promocode not active: {usage.promocode_code}")
        raise HTTPException(status_code=400, detail="Promocode not active")
    
    # Проверяем, не использовал ли пользователь промокод
    if db.query(PromocodeUsage).filter(
        PromocodeUsage.user_id == usage.user_id,
        PromocodeUsage.promocode_code == usage.promocode_code
    ).first():
        logger.error(f"Promocode already used by user: {usage.promocode_code}, user_id={usage.user_id}")
        raise HTTPException(status_code=400, detail="Promocode already used")
    
    # Проверяем ограничение max_usage
    if promocode.max_usage > 0:
        usage_count = db.query(PromocodeUsage).filter(
            PromocodeUsage.promocode_code == promocode.code
        ).count()
        if usage_count >= promocode.max_usage:
            db.delete(promocode)
            db.commit()
            logger.info(f"Promocode deleted: {promocode.code}, max_usage reached ({usage_count}/{promocode.max_usage})")
            raise HTTPException(status_code=400, detail="Промокод достиг максимального количества использований")
    
    new_usage = PromocodeUsage(
        user_id=usage.user_id,
        promocode_code=usage.promocode_code
    )
    db.add(new_usage)
    db.commit()
    
    # Проверяем, нужно ли деактивировать после добавления
    if promocode.max_usage > 0:
        usage_count = db.query(PromocodeUsage).filter(
            PromocodeUsage.promocode_code == promocode.code
        ).count()
        if usage_count >= promocode.max_usage:
            db.delete(promocode)
            db.commit()
            logger.info(f"Promocode deleted: {promocode.code}, max_usage reached ({usage_count}/{promocode.max_usage})")
            # Уведомление админов будет отправлено из handlers/devices.py
    
    logger.info(f"Promocode usage logged: user_id={usage.user_id}, code={usage.promocode_code}")
    return {"status": "success"}

@router.delete("/promocodes/{code}")
async def delete_promocode(
    code: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Deleting promocode: {code}")
    
    promocode = db.query(Promocode).filter(Promocode.code == code).first()
    if not promocode:
        logger.error(f"Promocode not found: {code}")
        raise HTTPException(status_code=404, detail="Promocode not found")
    
    usage_count = db.query(PromocodeUsage).filter(
        PromocodeUsage.promocode_code == code
    ).count()
    
    db.delete(promocode)  # Удаляет промокод и связанные promocode_usages (ON DELETE CASCADE)
    db.commit()
    
    logger.info(f"Promocode deleted: {code}, removed {usage_count} promocode_usages")
    return {"status": "success", "usage_count": usage_count}

@router.post("/outline/servers")
async def create_outline_server(
    server: OutlineServerCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Creating outline server: {server.api_url} with key_limit={server.key_limit}")
    
    api_url_str = str(server.api_url)
    if db.query(OutlineServer).filter(OutlineServer.api_url == api_url_str).first():
        logger.error(f"Server already exists: {api_url_str}")
        raise HTTPException(
            status_code=400,
            detail="Server with this URL already exists"
        )
    
    db_server = OutlineServer(
        api_url=api_url_str,
        cert_sha256=server.cert_sha256,
        key_count=0,
        key_limit=server.key_limit,
        is_active=True
    )
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    
    logger.info(f"Outline server created: {api_url_str} with key_limit={server.key_limit}")
    return {"status": "success", "server_id": db_server.id}

@router.get("/outline/servers")
async def get_outline_servers(
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info("Fetching outline servers")
    
    servers = db.query(OutlineServer).all()
    result = [
        {
            "id": server.id,
            "api_url": server.api_url,
            "cert_sha256": server.cert_sha256,
            "key_count": server.key_count,
            "key_limit": server.key_limit,
            "is_active": server.is_active,
            "created_at": server.created_at.strftime("%Y-%m-%d %H:%M")
        }
        for server in servers
    ]
    
    logger.info(f"Returning {len(result)} outline servers")
    return result

@router.delete("/outline/servers/{server_id}")
async def delete_outline_server(
    server_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Deleting outline server: {server_id}")
    
    server = db.query(OutlineServer).filter(OutlineServer.id == server_id).first()
    if not server:
        logger.error(f"Server not found: {server_id}")
        raise HTTPException(status_code=404, detail="Server not found")
    
    db.delete(server)
    db.commit()
    
    logger.info(f"Outline server deleted: {server_id}")
    return {"status": "success"}
