from asyncio.events import BaseDefaultEventLoopPolicy
import aiohttp
import asyncio
import logging
import json
from typing import Optional, Dict, Any
from datetime import datetime
from config import get_config, Backend

backend = get_config(Backend, "backend")
api_key = backend.key
url = backend.url

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Base URL for the API
BASE_URL = url
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

async def get_device_key(user_id: int, device: str) -> Optional[str]:
    url = f"{BASE_URL}/device/key"
    request_payload = {
            "user_id": user_id,
            "device": device
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, json=request_payload) as response:
                status = response.status
                response_json = await response.json()
                logger.info(f"Add device {device}, user: {user_id}. Status: {status}")
                logger.info(json.dumps(response_json))
                return response_json
        except aiohttp.BaseDefaultEventLoopPolicyhttp.ClientError as e:
            logger.error(f"Add Device: Error - {e}")

async def remove_device_key(user_id: int, device: str) -> Optional[str]:
    url = f"{BASE_URL}/device/key"
    request_payload = {
            "user_id": user_id,
            "device": device
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.delete(url, headers=HEADERS, json=request_payload) as response:
                status = response.status
                response_json = await response.json()
                logger.info(f"Remove device {device}, user: {user_id}. Status: {status}")
                logger.info(json.dumps(response_json))
                return response_json
        except aiohttp.ClientError as e:
            logger.error(f"Remove Device: Error - {e}")


