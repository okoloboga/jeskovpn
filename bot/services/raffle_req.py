import aiohttp
from typing import Optional, Dict, List, Any
import logging
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

async def get_active_raffles(raffle_id: Optional[int] = None) -> Optional[List[Dict[str, Any]]]:
    """GET /raffles or /raffles/{raffle_id}"""
    url = f"{BASE_URL}/raffles" if raffle_id is None else f"{BASE_URL}/raffles/{raffle_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                status = response.status
                if status in (200, 201):
                    response_json = await response.json()
                    return response_json if raffle_id else response_json.get("raffles", [])
                else:
                    text = await response.text()
                    logger.error(f"Get Raffles: Failed with status {status}, response: {text}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Get Raffles: Error - {e}")
            return None

async def create_raffle(raffle: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """POST /raffles"""
    url = f"{BASE_URL}/raffles"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, json=raffle) as response:
                status = response.status
                response_json = await response.json()
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Create Raffle: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Create Raffle: Error - {e}")
            return None

async def update_raffle(raffle_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """PATCH /raffles/{raffle_id}"""
    url = f"{BASE_URL}/raffles/{raffle_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.patch(url, headers=HEADERS, json=update_data) as response:
                status = response.status
                response_json = await response.json()
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Update Raffle: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Update Raffle: Error - {e}")
            return None

async def buy_tickets(raffle_id: int, user_id: int, count: int) -> Optional[Dict[str, Any]]:
    """POST /raffles/{raffle_id}/tickets"""
    url = f"{BASE_URL}/raffles/{raffle_id}/tickets"
    payload = {"user_id": user_id, "count": count}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, json=payload) as response:
                status = response.status
                response_json = await response.json()
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Buy Tickets: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Buy Tickets: Error - {e}")
            return None

async def set_winners(raffle_id: int, winner_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """POST /raffles/{raffle_id}/winners"""
    url = f"{BASE_URL}/raffles/{raffle_id}/winners"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, json=winner_data) as response:
                status = response.status
                response_json = await response.json()
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Set Winners: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Set Winners: Error - {e}")
            return None

async def add_tickets(raffle_id: int, ticket_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """POST /raffles/{raffle_id}/add-tickets"""
    url = f"{BASE_URL}/raffles/{raffle_id}/add-tickets"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=HEADERS, json=ticket_data) as response:
                status = response.status
                response_json = await response.json()
                if status in (200, 201):
                    return response_json
                else:
                    logger.error(f"Add Tickets: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Add Tickets: Error - {e}")
            return None

async def get_tickets(raffle_id: int, page: int = 0, per_page: int = 10) -> Optional[List[Dict[str, Any]]]:
    """GET /raffles/{raffle_id}/tickets"""
    url = f"{BASE_URL}/raffles/{raffle_id}/tickets?page={page}&per_page={per_page}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                status = response.status
                if status in (200, 201):
                    response_json = await response.json()
                    return response_json.get("tickets", [])
                else:
                    logger.error(f"Get Tickets: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Get Tickets: Error - {e}")
            return None

async def get_user_tickets(raffle_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """GET /raffles/{raffle_id}/tickets/user/{user_id}"""
    url = f"{BASE_URL}/raffles/{raffle_id}/tickets/user/{user_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                status = response.status
                if status == 200:
                    response_json = await response.json()
                    return response_json
                else:
                    logger.error(f"Get User Tickets: Failed with status {status}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Get User Tickets: Error - {e}")
            return None
