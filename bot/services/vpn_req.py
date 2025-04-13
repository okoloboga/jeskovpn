import requests

from typing import Optional, Dict, Any
from datetime import datetime

async def get_device_key(user_id: int, device: str) -> Optional[str]:
    """Mock VPN device key."""
    return f"vpn_key_{user_id}_{device}"
