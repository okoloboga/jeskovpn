from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any
from datetime import datetime, timezone
import uuid
import copy

from app.core.logging import logger
from app.core.security import get_api_key
from app.db.session import get_db
from app.db.models import User, Device, Subscription
from app.schemas.device import DeviceKeyCreate, DeviceKeyGet, DeviceKeyPut, DeviceKeyDelete, DeviceUsersResponse, UserDevicesResponse, \
                               DeviceUsersResponse, UserDevicesResponse
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

    # Check if device name already exists
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
    current_time = datetime.now(timezone.utc)
    combo_size = 0
    if device_data.slot == "combo":
        # Find active combo subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == device_data.user_id,
            Subscription.type == "combo",
            Subscription.end_date > current_time,
            Subscription.is_active == True
        ).first()
        
        if subscription:
            combo_size = subscription.combo_size
        else:
            # Find last non-active subscription
            last_subscription = db.query(Subscription).filter(
                Subscription.user_id == device_data.user_id,
                Subscription.type == "combo"
            ).order_by(Subscription.end_date.desc()).first()
            combo_size = last_subscription.combo_size if last_subscription else 5  # Default to 5 if no previous subscription
    else:
        # For device or router, combo_size remains 0
        subscription = db.query(Subscription).filter(
            Subscription.user_id == device_data.user_id,
            Subscription.type == device_data.slot,
            Subscription.combo_size == combo_size,
            Subscription.end_date > current_time,
            Subscription.is_active == True
        ).first()

    if not subscription:
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
    vpn_key, outline_key_id = await create_outline_key(outline_api_url, outline_cert_sha256)
    # vpn_key, outline_key_id = 'vpn_key', 'outline_key_id'

    # Create device record
    db_device = Device(
        user_id=device_data.user_id,
        device=device_data.slot,  # Use slot as device type
        device_name=device_data.device_name,
        vpn_key=vpn_key,
        outline_key_id=outline_key_id,
        start_date=subscription.start_date,
        end_date=subscription.end_date,
        created_at=datetime.now(timezone.utc)
    )
    
    db.add(db_device)
    db.commit()
    
    logger.info(f"Key generated successfully: user_id={device_data.user_id}, device={device_data.device}")
    return {"key": vpn_key}

@router.get("/active/{user_id}", response_model=UserDevicesResponse)
async def get_user_devices(
    user_id: int,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    logger.info(f"Fetching devices for user_id={user_id}")
    
    devices = db.query(Device).filter(Device.user_id == user_id).all()
    
    response = {
        "device": [],
        "router": [],
        "combo": []
    }
    
    for device in devices:
        device_response = DeviceUsersResponse(
            device=device.device,
            device_name=device.device_name,
            device_type=device.device
        )
        if device.device == "device":
            response["device"].append(device_response)
        elif device.device == "router":
            response["router"].append(device_response)
        elif device.device == "combo":
            response["combo"].append(device_response)
    
    logger.info(f"Returning devices for user_id={user_id}: {len(devices)} devices")
    return response

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

    # Check if device exists
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
    
    # Check if new device name already exists
    existing_device = db.query(Device).filter(
        Device.user_id == device_data.user_id,
        Device.device_name == device_data.device_new_name
    ).first()

    if existing_device:
        logger.error(f"Device name {device_data.device_new_name} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device name already exists"
        )

    # Update device name
    device.device_name = device_data.device_new_name
    
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
    
    # Delete device record
    db.delete(device)
    db.commit()
    
    logger.info(f"Key removed successfully: user_id={device_data.user_id}, device_name={device_data.device_name}")
    return {"status": "Device removed"}

