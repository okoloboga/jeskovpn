import aiohttp
import asyncio
import logging
import json
from typing import Optional, Any
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

async def generate_device_key(user_id: int, device: str, device_name: str, slot: str) -> Optional[Any]:
    url = f"{BASE_URL}/devices/key"
    request_payload = {
        "user_id": user_id,
        "device": device,
        "device_name": device_name,
        "slot": slot
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, json=request_payload) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Add device {device}, user: {user_id}. Status: {status}")
                # logger.info(json.dumps(response_json))
                if status in (200, 201):
                    return response_json
                elif status == 409:
                    return "already_exists"
                else:
                    logger.error(f"Add Device: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Add Device: Error - {e}")
            return None

async def get_device_key(user_id: int, device_name: str) -> Optional[Any]:
    url = f"{BASE_URL}/devices/key"
    request_payload = {
        "user_id": user_id,
        "device_name": device_name,
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS, json=request_payload) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Get device {device_name}, user: {user_id}. Status: {status}")
                # logger.info(json.dumps(response_json))
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Get Device: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Get Device: Error - {e}")
            return None

async def rename_device(user_id: int, device_old_name: str, device_new_name: str) -> Optional[Any]:
    url = f"{BASE_URL}/devices/key"
    request_payload = {
        "user_id": user_id,
        "device_old_name": device_old_name,
        "device_new_name": device_new_name
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.put(url, headers=HEADERS, json=request_payload) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Rename device {device_old_name} to {device_new_name}, user: {user_id}. Status: {status}")
                # logger.info(json.dumps(response_json))
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Rename Device: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Rename Device: Error - {e}")
            return None

async def remove_device_key(user_id: int, device_name: str) -> Optional[Any]:
    url = f"{BASE_URL}/devices/key"
    request_payload = {
        "user_id": user_id,
        "device_name": device_name
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.delete(url, headers=HEADERS, json=request_payload) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Remove device {device_name}, user: {user_id}. Status: {status}")
                # logger.info(json.dumps(response_json))
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Remove Device: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Remove Device: Error - {e}")
            return None
