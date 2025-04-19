import aiohttp
import asyncio
import json
import logging
from typing import Dict, Optional

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

async def delete_ticket(user_id: int) -> Tuple[int, Union[Dict, str]]:
    """Test DELETE /api/tickets/{user_id}"""
    url = f"{BASE_URL}/api/tickets/{user_id}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.delete(url, headers=HEADERS) as response:
                status = response.status
                response_json = await response.json()
                logger.info(f"Delete Ticket: Status {status}")
                logger.info(json.dumps(response_json, indent=2))
                return status, response_json
        except aiohttp.ClientError as e:
            logger.error(f"Delete Ticket: Error - {e}")
            return 0, str(e)

# async def delete_ticket(user_id: int) -> None:
#     """Mock ticket deletion."""
#     print(f"Deleted ticket for user {user_id}")
