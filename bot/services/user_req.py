import aiohttp
import asyncio
import re
import json
import logging
from typing import Dict, Optional, Any
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

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """GET /users/{user_id}"""
    url = f"{BASE_URL}/users/{user_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Get User: Status {status}")
                # logger.info(json.dumps(response_json, indent=2))
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Get User: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Get User: Error - {e}")
            return None

async def create_user(
    user_id: int, first_name: str, last_name: str, username: str, payload: Optional[Dict] = None
) -> Optional[Dict[str, Any]]:
    """POST /users/create"""
    url = f"{BASE_URL}/users/create"
    default_payload = {
        "user_id": user_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username
    }
    request_payload = payload if payload is not None else default_payload

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, json=request_payload) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Create User: Status {status}")
                # logger.info(json.dumps(response_json, indent=2))
                if status in (200, 201, 409):
                    return response_json
                else:
                    logger.error(f"Create User: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Create User: Error - {e}")
            return None

async def add_referral(
    inviter_id: int, user_id: int, payload: Optional[Dict] = None
) -> Optional[Dict[str, Any]]:
    """POST /referrals"""
    url = f"{BASE_URL}/referrals"
    default_payload = {
        "inviter_id": str(inviter_id),
        "user_id": str(user_id)
    }
    request_payload = payload if payload is not None else default_payload

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, json=request_payload) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Add Referral: Status {status}")
                # logger.info(json.dumps(response_json, indent=2))
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Add Referral: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Add Referral: Error - {e}")
            return None

async def get_user_devices(user_id: int) -> Optional[Dict[str, Any]]:
    """GET /devices/active/{user_id}"""
    url = f"{BASE_URL}/devices/active/{user_id}"
    
    logger.info(f"Sending request to backend: GET {url}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Get User Devices: Status {status}")
                # logger.info(json.dumps(response_json, indent=2))
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Get User Devices: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Get User Devices: Error - {e}")
            return None

async def get_user_contact(user_id: int) -> Optional[Dict[str, Any]]:
    """
    GET /users/contact?user_id=...
    """
    params = {"user_id": user_id}
    url = f"{BASE_URL}/users/contact"

    logger.info(f"Sending GET request to {url} with params: {params}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS, params=params) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Get User Contact: Status {status}")
                # logger.info(json.dumps(response_json, indent=2))
                if status == 200 and isinstance(response_json, dict):
                    return response_json
                else:
                    logger.error(f"Get User Contact: Failed with status {status}, response: {response_json}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Get User Contact: Error - {e}")
            return None

async def update_user_contact(
        user_id: int, contact_type: str, contact: str
) -> Optional[Dict[str, Any]]:
    """
    POST /users/contact
    {
        "user_id": ...,
        "contact_type": "email" or "phone",
        "contact": "..."
    }
    """
    normalized_contact = contact
    if contact_type.lower() == "phone":
        # Нормализация: удаляем пробелы, тире, скобки, знак "+"
        normalized_contact = re.sub(r'[\s\-\(\)+]', '', contact)
        # Базовая проверка перед отправкой
        if not (normalized_contact.isdigit() and len(normalized_contact) in [10, 11]):
            logger.error(f"Invalid phone number format before sending: {contact}")
            return None
        # Если номер начинается с "+7" или "8", заменяем на "7"
        if normalized_contact.startswith('8'):
            normalized_contact = '7' + normalized_contact[1:]
        elif normalized_contact.startswith('7') and len(normalized_contact) == 11:
            pass  # Уже в нужном формате
        else:
            logger.error(f"Phone number must start with 7 or 8: {normalized_contact}")
            return None

    payload = {
        "user_id": user_id,
        "contact_type": contact_type,
        "contact": normalized_contact
    }

    url = f"{BASE_URL}/users/contact"

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, json=payload) as response:
                status = response.status
                response_json = await response.json()
                # logger.info(f"Update User Contact: Status {status}")
                # logger.info(json.dumps(response_json, indent=2))
                if status == 200:
                    return response_json
                else:
                    logger.error(f"Update User Contact: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Update User Contact: Error - {e}")
            return None
