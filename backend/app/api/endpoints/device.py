from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
import uuid
import copy

from app.core.logging import logger
from app.core.security import get_api_key
from app.db.session import get_db
from app.db.models import User, Device
from app.schemas.device import DeviceKeyCreate, DeviceKeyGet, DeviceKeyDelete

router = APIRouter()

@router.post("/key", status_code=status.HTTP_200_OK)
async def generate_key(
    device_data: DeviceKeyCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
) -> dict:
    logger.info(f"Generating key: user_id={device_data.user_id}, device={device_data.device}, device_name={device_data.device_name}, slot={device_data.slot}")
    
    # Check if user exists
    user = db.query(User).filter(User.user_id == device_data.user_id).first()
    if not user:
        logger.error(f"User with ID {device_data.user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    existing_device = db.query(Device).filter(
            Device.user_id == device_data.user_id,
            Device.device_name == device_data.device_name
        ).first()
    if existing_device:
        logger.error(f"Device name '{device_data.device_name}' already exists for user {device_data.user_id}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device name already exists for this user"
        )
    
    # Check if user has an active subscription
    subscription = copy.deepcopy(user.subscription)
    has_subscription = False

    logger.info(f'Users subscription {subscription}')
    
    if device_data.slot == "device" and subscription["device"]["duration"] > 0:
        has_subscription = True
    elif device_data.slot == "router" and subscription["router"]["duration"] > 0:
        has_subscription = True
    elif device_data.slot == "combo" and subscription["combo"]["duration"] > 0:
        has_subscription = True
    
    if not has_subscription:
        logger.error(f"No active subscription for user {device_data.user_id} and slot {device_data.slot}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No active subscription"
        )
    
    # Generate a dummy VPN key (in a real app, this would call the Outline API)
    vpn_key = f"{uuid.uuid4().hex}"
    outline_key_id = str(uuid.uuid4())
    
    # Create device record
    db_device = Device(
        user_id=device_data.user_id,
        device=device_data.device,
        device_name=device_data.device_name,
        vpn_key=vpn_key,
        outline_key_id=outline_key_id
    )
    
    db.add(db_device)
    
    # Update user's subscription to add the device
    subscription[device_data.slot]["devices"].append(device_data.device_name)

    user.subscription = subscription
    db.commit()
    
    logger.info(f"Key generated successfully: user_id={device_data.user_id}, device={device_data.device}")
    return {"key": vpn_key}

@router.get("/key", status_code=status.HTTP_200_OK)
async def get_key(
    device_data: DeviceKeyGet,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
) -> Any:
    logger.info(f"Getting key: user_id={device_data.user_id}, device_name={device_data.device_name}")
    
    # Check if device exists
    device = db.query(Device).filter(
        Device.user_id == device_data.user_id,
        Device.device_name == device_data.device_name
    ).first()
    
    if not device:
        logger.error(f"Device {device_data.device_name} not found for user {device_data.user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    logger.info(f"Key retrieved successfully: user_id={device_data.user_id}, device_name={device_data.device_name}, device_type={device.device}")
    return {"key": device.vpn_key,
            "device_type": device.device}

@router.delete("/key", status_code=status.HTTP_200_OK)
async def remove_key(
    device_data: DeviceKeyDelete,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
) -> Any:
    logger.info(f"Removing key: user_id={device_data.user_id}, device_name={device_data.device_name}")
    
    # Check if device exists
    device = db.query(Device).filter(
        Device.user_id == device_data.user_id,
        Device.device_name == device_data.device_name
    ).first()
    
    if not device:
        logger.error(f"Device {device_data.device_name} not found for user {device_data.user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Remove device from user's subscription
    user = db.query(User).filter(User.user_id == device_data.user_id).first()
    subscription = copy.deepcopy(user.subscription)
    
    # Check in which subscription type the device exists
    for sub_type in ["device", "router", "combo"]:
        if device_data.device_name in subscription[sub_type]["devices"]:
            subscription[sub_type]["devices"].remove(device_data.device_name)
    
    user.subscription = subscription
    
    # Delete device record
    db.delete(device)
    db.commit()
    
    logger.info(f"Key removed successfully: user_id={device_data.user_id}, device_name={device_data.device_name}")
    return {"status": "Device removed"}
