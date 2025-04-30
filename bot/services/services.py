import logging
import re
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
    "device": {"0": 0, "1": 100, "3": 400, "6": 625, "12": 900},
    "router": {"0": 0, "1": 350, "3": 945, "6": 1470, "12": 2100},
    "combo": {"0": {"0": 0},
              "5": {"0": 0, "1": 750, "3": 2000, "6": 3150, "12": 4500},
              "10": {"0": 0, "1": 1500, "3": 4000, "6": 6300, "12": 9000}
        }
    }
MONTH_DAY = 30.42

DAY_PRICE =  {
    "device": {"0": 0.0, "1": 5.0, "3": 4.4, "6": 3.45, "12": 2.46},
    "router": {"0": 0.0, "1": 11.66, "3": 10.5, "6": 8.12, "12": 5.75},
    "combo": {"0": {"0": 0.0},
              "5": {"0": 0.0, "1": 5.0, "3": 22.0, "6": 17.4, "12": 12.33},
              "10":  {"0": 0.0, "1": 10, "3": 4.4, "6": 34.8, "12": 24.66}
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

async def get_user_info(user_id: int) -> dict | None:

    user = await get_user_data(user_id)

    logger.info(f'USER: {user}')
    
    if user is None:
        return None

    try:
        device_duration = user['subscription']['device']['duration']
        router_duration = user['subscription']['router']['duration']
        combo_duration = user['subscription']['combo']['duration']
        combo_type = user['subscription']['combo']['type']
        devices_count = len(user['subscription']['device']['devices'])
        routers_count = len(user['subscription']['router']['devices'])
        combo_count = len(user['subscription']['combo']['devices'])
        devices_list = user['subscription']['device']['devices']
        router = str(user['subscription']['router']['duration'])
        combo_devices = user['subscription']['combo']['devices']

        if device_duration == 0 and router_duration == 0 and combo_duration == 0:
            day_price = 0
        else:
            if int(device_duration) != 0:
                devices_price = devices_count * (MONTH_PRICE['device'][str(device_duration)] / int(device_duration) * MONTH_DAY)
            else:
                devices_price = 0
            if int(router_duration) != 0:
                router_price = routers_count * (MONTH_PRICE['router'][str(router_duration)] / int(router_duration) * MONTH_DAY)
            else:
                router_price = 0
            if int(combo_type) != 0 and int(combo_duration) != 0:
                combo_price = combo_count * (MONTH_PRICE['combo'][str(combo_type)][str(combo_duration)] / int(combo_type) / int(combo_duration) * MONTH_DAY)
            else:
                combo_price = 0

            day_price = devices_price + router_price + combo_price
        
        if combo_type != '0' and str(combo_duration) != '0':
            combo_count = len(user['subscription']['combo']['devices'])
        else:
            combo_count = 0
        total_devices = devices_count + routers_count + combo_count
        devices_list += combo_devices

        if router != "0":
            devices_list += ['router']

        durations = (device_duration, router_duration, combo_duration)
        if int(device_duration) + int(router_duration) + int(combo_duration) == 0:
            is_subscribed = False
        else:
            is_subscribed = True

        result = {'day_price': day_price,
                  'total_devices': total_devices,
                  'devices_list': devices_list,
                  'durations': durations,
                  'is_subscribed': is_subscribed}

        return result
 
    except Exception as e:
        logger.error(f"Failed to count total_day_price {user_id}: {e}")
        raise

async def check_slot(user_id: int, device: str) -> str:

    user_info = await get_user_info(user_id)
    user_data = await get_user_data(user_id)
    
    if user_info is None or user_data is None:
        return 'no_user'

    DEVICES = ['android', 'iphone/ipad', 'windows', 'macos', 'tv']
    
    if (user_info['durations'][0] == user_info['durations'][1] == user_info['durations'][2] == 0) or (
            user_info['durations'][1] == 0 and device == 'router') or (
                    user_info['durations'][0] == 0 and user_info['durations'][2] == 0 and device in DEVICES):
        return 'no_subscription'
    elif user_info['durations'][2] != 0:
        combo_type = user_data['subscription']['combo']['type']
        combo_fullnes = user_data['subscription']['combo']['devices']
        if combo_fullnes >= combo_type and device in DEVICES and user_info['durations'][0] != 0:
            return 'device'
        elif combo_fullnes >= combo_type and device == 'router' and user_info['durations'][1] != 0:
            return 'router'    
        return 'combo'
    elif user_info['durations'][0] != 0 and device in DEVICES:
        return 'device'
    elif user_info['durations'][1] != 0 and device == 'router':
        return 'router'
    else:
        return 'error'

def validate_device_name(name: str) -> str:
    
    stripped_name = name.strip()
    pattern = r'^[a-zA-Za-яА-ЯёЁ0-9\s]+$'
    correct_pattern = bool(re.match(pattern, stripped_name))
    dash_replace = stripped_name.replace(" ", "_")
    correct_len = len(dash_replace.encode("utf-8")) <= 32

    if not correct_pattern:
        return 'wrong_pattern'
    elif not correct_len:
        return 'wrong_len'
    else:
        return dash_replace


