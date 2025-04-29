import aiohttp
import asyncio
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
                logger.info(f"Get User: Status {status}")
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
                logger.info(f"Create User: Status {status}")
                logger.info(json.dumps(response_json, indent=2))
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
                logger.info(f"Add Referral: Status {status}")
                logger.info(json.dumps(response_json, indent=2))
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Add Referral: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Add Referral: Error - {e}")
            return None

# async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
#     """Mock user data."""
#     return {
#         "user_id": user_id,
#         "balance": 500.0,
#         "subscription": {'device': {'devices': ['android', 'iphone'],
#                                     'duration': 3},
#                          'router': {'duration': 0},
#                          'combo': {'devices': [],
#                                    'duration': 0,
#                                    'type': 0}
#                         }
#         }

# async def create_user(user_id: int, first_name: str, last_name: str, username: str) -> None:
#     """Mock user creation."""
#     print(f"Created user {user_id}: {first_name} {last_name} (@{username})")

# async def add_referral(payload: str, user_id: str) -> None:
#     """Mock referral addition."""
#     print(f"Added referral {payload} for user {user_id}")

# async def send_ticket(content: str, user_id: int, username: str) -> None:
#     """Mock ticket creation."""
#     print(f"Ticket from user {user_id} (@{username}): {content}")

# async def get_ticket_by_id(user_id: int) -> Optional[Dict[str, Any]]:
#     """Mock ticket retrieval."""
#     return {"user_id": user_id, "content": "Sample ticket", "created_at": datetime.utcnow().isoformat()}
