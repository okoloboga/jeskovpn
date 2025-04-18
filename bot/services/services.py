import logging
from typing import Optional
from services import user_req

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s'
)

# Subscription prices in rubles
MONTH_PRICE = {
    "device": {"1": 149, "3": 400, "6": 625, "12": 900},
    "router": {"1": 350, "3": 945, "6": 1470, "12": 2100},
    "combo": {"0": {"0": 0},
              "5": {"0": 0, "1": 750, "3": 2000, "6": 3150, "12": 4500},
              "10": {"0": 0, "1": 1500, "3": 4000, "6": 6300, "12": 9000}
        }
    }

DAY_PRICE =  {
    "device": {"0": 0.0, "1": 5.0, "3": 4.4, "6": 3.45, "12": 2.46},
    "router": {"0": 0.0, "1": 11.66, "3": 10.5, "6": 8.12, "12": 5.75},
    "combo": {"0": {"0": 0.0},
              "5": {"0": 0.0, "1": 25.0, "3": 22.0, "6": 17.4, "12": 12.33},
              "10":  {"0": 0.0, "1": 50, "3": 44, "6": 34.8, "12": 24.66}
        }
    }

async def get_user_data(user_id: int) -> Optional[dict]:
    """
    Fetch user data from the backend.

    Args:
        user_id (int): Telegram user ID.

    Returns:
        Optional[dict]: User data if found, None otherwise.

    Raises:
        Exception: If backend request fails.
    """
    try:
        user = await user_req.get_user(user_id)
        if user is None:
            logger.warning(f"User {user_id} not found in backend")
            return None
        return {
            "balance": user['balance'],
            "subscription": user['subscription']
        }
    except Exception as e:
        logger.error(f"Failed to fetch user {user_id}: {e}")
        raise

async def day_price(user_id: int) -> float | int:

    user = await get_user_data(user_id)
    
    if user is None:
        return 0
    try:
        device_duration = user['subscription']['device']['duration']
        router_duration = user['subscription']['router']['duration']
        combo_duration = user['subscription']['combo']['duration']
        combo_type = user['subscription']['combo']['type']

        if device_duration == 0 and router_duration == 0 and combo_duration == 0:
            return 0
        
        devices_count = len(user['subscription']['device']['devices'])
        devices_price = devices_count * DAY_PRICE['device'][str(device_duration)]
        router_price = DAY_PRICE['router'][str(router_duration)]
        combo_price = DAY_PRICE['combo'][str(combo_type)][str(combo_duration)]

        total_day_price = devices_price + router_price + combo_price
        
        return total_day_price
 
    except Exception as e:
        logger.error(f"Failed to count total_day_price {user_id}: {e}")
        raise

async def count_devices(user_id: int) -> int:

    user = await get_user_data(user_id)

    if user is None:
        return 0
    try:
        devices_count = len(user['subscription']['device']['devices'])
        router_duration = user['subscription']['router']['duration']
        combo_duration = user['subscription']['combo']['duration']
        combo_type = user['subscription']['combo']['type']
        
        if combo_type != '0' and str(combo_duration) != '0':
            combo_count = len(user['subscription']['combo']['devices'])
        else:
            combo_count = 0
        router_count = 1 if str(router_duration) != "0" else 0

        total_devices = devices_count + router_count + combo_count

        return total_devices

    except Exception as e:
        logger.error(f"Failed to count total_day_price {user_id}: {e}")
        raise

async def user_devices(user_id: int) -> list:

    user = await get_user_data(user_id)

    if user is None:
        return []
    try:
        devices_list = user['subscription']['device']['devices']
        router = str(user['subscription']['router']['duration'])
        combo_devices = user['subscription']['combo']['devices']
        
        result_list = devices_list + combo_devices

        if router != "0":
            result_list += ['router']

        return result_list

    except Exception as e:
        logger.error(f"Failed to get devices list for user {user_id}: {e}")
        raise
        
