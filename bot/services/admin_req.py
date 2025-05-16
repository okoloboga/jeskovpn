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

async def get_users(skip: int = 0, limit: int = 20, user_id: Optional[int] = None):
    """GET /admin/users"""
    url = f"{BASE_URL}/admin/users?skip={skip}&limit={limit}"
    if user_id is not None:
        url += f"&user_id={user_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"get_users: {e}")
            return []

async def get_user_details(user_id: int):
    """GET /admin/users/{user_id}"""
    url = f"{BASE_URL}/admin/users/{user_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"get_user_details: {e}")
            return None

async def block_user(user_id: int) -> bool:
    """POST /admin/users/{user_id}/block"""
    url = f"{BASE_URL}/admin/users/{user_id}/block"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS) as response:
                return response.status in (200, 201)
        except Exception as e:
            logger.error(f"block_user: {e}")
            return False

async def remove_from_blacklist(user_id: int) -> bool:
    """DELETE /admin/blacklist/{user_id}"""
    url = f"{BASE_URL}/admin/blacklist/{user_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.delete(url, headers=HEADERS) as response:
                if response.status in (200, 201):
                    logger.debug(f"User {user_id} removed from blacklist")
                    return True
                logger.error(f"Failed to remove user {user_id} from blacklist: status {response.status}")
                return False
        except Exception as e:
            logger.error(f"remove_from_blacklist for user {user_id}: {e}")
            return False

async def delete_user(user_id: int) -> bool:
    """DELETE /admin/users/{user_id}"""
    url = f"{BASE_URL}/admin/users/{user_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.delete(url, headers=HEADERS) as response:
                return response.status == 204
        except Exception as e:
            logger.error(f"delete_user: {e}")
            return False

async def check_blacklist(user_id: int) -> bool:
    """GET /admin/blacklist/check"""
    url = f"{BASE_URL}/admin/blacklist/check?user_id={user_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                response_json = await response.json()
                return response_json.get("is_blocked", False)
        except Exception as e:
            logger.error(f"check_blacklist: {e}")
            return False

async def get_keys(skip: int = 0, limit: int = 20, vpn_key: Optional[str] = None):
    """GET /admin/devices"""
    url = f"{BASE_URL}/admin/devices?skip={skip}&limit={limit}"
    if vpn_key is not None:
        url += f"&vpn_key={vpn_key}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"get_keys: {e}")
            return []

async def get_key_history(vpn_key: str):
    """GET /admin/devices/history"""
    url = f"{BASE_URL}/admin/devices/history?vpn_key={vpn_key}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"get_key_history: {e}")
            return []

async def get_payments_summary():
    """GET /admin/payments/summary"""
    url = f"{BASE_URL}/admin/payments/summary"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"get_payments_summary: {e}")
            return None

async def get_all_users():
    """GET /admin/users/ids"""
    url = f"{BASE_URL}/admin/users/ids"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"get_all_users: {e}")
            return []

async def get_admins():
    """GET /admin/admins"""
    url = f"{BASE_URL}/admin/admins"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                return await response.json()
        except Exception as e:
            logger.error(f"get_admins: {e}")
            return []

async def add_admin(user_id: int) -> bool:
    """POST /admin/admins"""
    url = f"{BASE_URL}/admin/admins"
    payload = {"user_id": user_id}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, headers=HEADERS) as response:
                if response.status in (200, 201):
                    return True
                logger.error(f"Failed to add admin {user_id}: status {response.status}")
                return False
        except Exception as e:
            logger.error(f"add_admin: {e}")
            return False

async def delete_admin(user_id: int) -> bool:
    """DELETE /admin/admins/{user_id}"""
    url = f"{BASE_URL}/admin/admins/{user_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.delete(url, headers=HEADERS) as response:
                return response.status in (200, 204)
        except Exception as e:
            logger.error(f"delete_admin: {e}")
            return False

async def check_admin(user_id: int) -> bool:
    """GET /admin/admins/check"""
    url = f"{BASE_URL}/admin/admins/check?user_id={user_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                result = await response.json()
                return result.get("is_admin", False)
        except Exception as e:
            logger.error(f"check_admin: {e}")
            return False

async def is_user_blacklisted(user_id: int) -> bool:
    """GET /admin/blacklist/check"""
    url = f"{BASE_URL}/admin/blacklist/check?user_id={user_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                result = await response.json()
                return result.get("is_blacklisted", False)
        except Exception as e:
            logger.error(f"is_user_blacklisted: {e}")
            return False
