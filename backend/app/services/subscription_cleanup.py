import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.db.session import get_db
from app.db.models import Subscription, Device
from app.services.outline import delete_outline_key
from app.core.config import get_app_config

logger = logging.getLogger(__name__)

async def cleanup_expired_subscriptions(db: Session) -> dict:
    """
    Check for expired subscriptions and remove associated devices and VPN keys.
    
    Args:
        db: SQLAlchemy session
    
    Returns:
        Dict with counts of processed subscriptions and devices
    """
    logger.info("Starting cleanup of expired subscriptions")
    
    current_time = datetime.now(timezone.utc)
    config = get_app_config()
    outline_api_url = config.outline.api_url
    outline_cert_sha256 = config.outline.cert_sha256
    
    # Find expired or inactive subscriptions
    expired_subscriptions = db.query(Subscription).filter(
        (Subscription.end_date < current_time) | (Subscription.is_active == False)
    ).all()
    
    stats = {
        "subscriptions_processed": 0,
        "devices_deleted": 0,
        "keys_deleted": 0,
        "errors": 0
    }
    
    for sub in expired_subscriptions:
        logger.info(f"Processing subscription: id={sub.id}, user_id={sub.user_id}, type={sub.type}")
        
        # Find associated devices
        devices = db.query(Device).filter(
            Device.user_id == sub.user_id,
            Device.device == sub.type
        ).all()
        
        # Delete devices and their VPN keys
        for device in devices:
            if device.outline_key_id:
                try:
                    await delete_outline_key(outline_api_url, outline_cert_sha256, device.outline_key_id)
                    logger.info(f"Deleted VPN key for device: id={device.id}, outline_key_id={device.outline_key_id}")
                    stats["keys_deleted"] += 1
                except HTTPException as e:
                    logger.error(f"Failed to delete VPN key for device id={device.id}: {e.detail}")
                    stats["errors"] += 1
                    continue
            
            db.delete(device)
            stats["devices_deleted"] += 1
            logger.info(f"Deleted device: id={device.id}, device_name={device.device_name}")
        
        # Mark subscription as inactive
        sub.is_active = False
        stats["subscriptions_processed"] += 1
        logger.info(f"Marked subscription as inactive: id={sub.id}")
    
    db.commit()
    
    logger.info(f"Cleanup completed: {stats}")
    return stats
