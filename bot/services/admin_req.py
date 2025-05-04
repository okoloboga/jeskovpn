import aiohttp
import asyncio
import json
import logging
from typing import Dict, Optional, Tuple, Union

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

async def has_admin_password(admin_id: int) -> bool:
    """GET /admin/has_password"""
    url = f"{BASE_URL}/admin/has_password?admin_id={admin_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                status = response.status
                response_json = await response.json()
                logger.info(f"Has Admin Password: Status {status}")
                return response_json.get("has_password", False)
        except aiohttp.ClientError as e:
            logger.error(f"Has Admin Password: Error - {e}")
            return False

async def set_admin_password(admin_id: int, password: str) -> bool:
    """POST /admin/set_password"""
    url = f"{BASE_URL}/admin/set_password"
    payload = {"admin_id": admin_id, "password": password}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, headers=HEADERS) as response:
                status = response.status
                logger.info(f"Set Admin Password: Status {status}")
                return status in (200, 201)
        except aiohttp.ClientError as e:
            logger.error(f"Set Admin Password: Error - {e}")
            return False

async def check_admin_password(admin_id: int, password: str) -> bool:
    """POST /admin/check_password"""
    url = f"{BASE_URL}/admin/check_password"
    payload = {"admin_id": admin_id, "password": password}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, headers=HEADERS) as response:
                status = response.status
                logger.info(f"Check Admin Password: Status {status}")
                return status in (200, 201)
        except aiohttp.ClientError as e:
            logger.error(f"Check Admin Password: Error - {e}")
            return False

async def get_users_summary():
    """GET /admin/users/summary"""
    url = f"{BASE_URL}/admin/users/summary"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"get_users_summary: {e}")
            return None

async def get_users(skip=0, limit=20):
    """GET /admin/users"""
    url = f"{BASE_URL}/admin/users?skip={skip}&limit={limit}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"get_users: {e}")
            return []
