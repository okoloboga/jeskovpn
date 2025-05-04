from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
import uuid
import copy

from app.core.logging import logger
from app.core.security import get_api_key
from app.db.session import get_db
from app.db.models import User, Device
from app.schemas.device import DeviceKeyCreate, DeviceKeyGet, DeviceKeyPut, DeviceKeyDelete
from app.services.outline import create_outline_key
from app.core.config import get_app_config

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
    
    # Get Outline API configuration
    config = get_app_config()
    outline_api_url = config.outline.api_url
    outline_cert_sha256 = config.outline.cert_sha256

    # Generate VPN key using Outline API
    # vpn_key, outline_key_id = await create_outline_key(outline_api_url, outline_cert_sha256)
    vpn_key, outline_key_id = 'vpn_key', 'outline_key_id'

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

@router.put("/key", status_code=status.HTTP_200_OK)
async def rename_device(
        device_data: DeviceKeyPut,
        db: Session = Depends(get_db),
        api_key: str = Depends(get_api_key)
) -> Any:
    logger.info(f"Rename device: user_id={device_data.user_id}, device_old_name={device_data.device_old_name}, device_new_name={device_data.device_new_name}")

    device = db.query(Device).filter(
        Device.user_id == device_data.user_id,
        Device.device_name == device_data.device_old_name
    ).first()

    if not device:
        logger.error(f"Device {device_data.device_old_name} not found for user {device_data.user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    existing_device = db.query(Device).filter(
        Device.device_name == device_data.device_new_name
    ).first()

    if existing_device:
        logger.error(f"Device name {device_data.device_new_name} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device name already exists"
        )

    device.device_name = device_data.device_new_name

    # Update device name in user's subscription
    user = db.query(User).filter(User.user_id == device_data.user_id).first()
    subscription = copy.deepcopy(user.subscription)

    for sub_type in ["device", "router", "combo"]:
        if device_data.device_old_name in subscription[sub_type]["devices"]:
            subscription[sub_type]["devices"].remove(device_data.device_old_name)
            subscription[sub_type]["devices"].append(device_data.device_new_name)
    
    user.subscription = subscription
    
    db.commit()
    db.refresh(device)

    logger.info(f"Device renamed successfully: {device_data.device_old_name} to {device_data.device_new_name} for user {device_data.user_id}")
    return {"status": "Device renamed"}

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
