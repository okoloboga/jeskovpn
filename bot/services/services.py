import logging
import re
import asyncio

from aiogram import Bot
from typing import Dict, Optional
from services import user_req, payment_req

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s'
)

# Subscription prices in rubles
MONTH_PRICE = {
    "device": {"0": 0, "1": 100, "3": 240, "6": 420, "12": 600},
    "router": {"0": 0, "1": 250, "3": 600, "6": 1000, "12": 1500},
    "combo": {"0": {"0": 0},
              "5": {"0": 0, "1": 500, "3": 1200, "6": 2100, "12": 3000},
              "10": {"0": 0, "1": 850, "3": 2000, "6": 3500, "12": 5000}
        }
    }

MONTH_PRICE_STARS = {
    "device": {"0": 0, "1": 55, "3": 130, "6": 230, "12": 330},
    "router": {"0": 0, "1": 140, "3": 335, "6": 590, "12": 840},
    "combo": {"0": {"0": 0},
              "5": {"0": 0, "1": 275, "3": 660, "6": 1155, "12": 1650},
              "10": {"0": 0, "1": 465, "3": 1120, "6": 1960, "12": 2800}
        }
    }

START_PRICE = 1.79
MONTH_DAY = 30.42

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
        # Get user balance
        user = await user_req.get_user(user_id)
        if user is None:
            logger.warning(f"User {user_id} not found in backend")
            return None
        
        # Get subscriptions
        subscriptions = await payment_req.get_subscriptions(user_id) or []
        
        # Get devices
        devices = await user_req.get_user_devices(user_id) or {
            "device": [], "router": [], "combo": []
        }
        
        # Form subscription in old format
        subscription = {
            "device": {"devices": [], "duration": 0},
            "router": {"devices": [], "duration": 0},
            "combo": {"devices": [], "duration": 0, "type": 0}
        }
        
        # Populate devices
        subscription["device"]["devices"] = [d["device_name"] for d in devices["device"]]
        subscription["router"]["devices"] = [d["device_name"] for d in devices["router"]]
        subscription["combo"]["devices"] = [d["device_name"] for d in devices["combo"]]
        
        logger.info(f'GET subscriptions: {subscriptions}')
        logger.info(f'GET devices: {devices}')

        # Populate durations and combo type
        for sub in subscriptions:
            if sub["type"] == "device":
                subscription["device"]["duration"] = sub["remaining_days"]
            elif sub["type"] == "router":
                subscription["router"]["duration"] = sub["remaining_days"]
            elif sub["type"] == "combo":
                subscription["combo"]["duration"] = sub["remaining_days"]
                subscription["combo"]["type"] = sub["combo_size"]
        
        return {
            "balance": user["balance"],
            "subscription": subscription
        }
    except Exception as e:
        logger.error(f"Failed to fetch user {user_id}: {e}")
        raise

async def get_user_info(user_id: int) -> Optional[Dict]:
    """
    Process user data to get subscription and device information.

    Args:
        user_id (int): Telegram user ID.

    Returns:
        Optional[Dict]: Processed user info or None if user not found.
    """
    user = await get_user_data(user_id)
    
    logger.info(f'USER: {user}')
    
    if user is None:
        return None

    try:
        device_duration = user['subscription']['device']['duration']
        router_duration = user['subscription']['router']['duration']
        combo_duration = user['subscription']['combo']['duration']
        combo_type = user['subscription']['combo']['type']
        devices_list = user['subscription']['device']['devices']
        routers_list = user['subscription']['router']['devices']
        combo_list = user['subscription']['combo']['devices']
        
        # Get monthly price from subscriptions
        subscriptions = await payment_req.get_subscriptions(user_id) or []
        month_price = 0.0
        for sub in subscriptions:
            month_price += float(sub["monthly_price"])
        
        total_devices = len(devices_list) + len(routers_list) + len(combo_list)
        all_list = (devices_list, routers_list, combo_list)
        durations = (device_duration, router_duration, combo_duration)
        
        is_subscribed = device_duration + router_duration + combo_duration > 0
        
        active_subscriptions: Dict = {}
        if device_duration > 0:
            active_subscriptions['devices'] = len(devices_list)
        if router_duration > 0:
            active_subscriptions['routers'] = len(routers_list)
        if combo_duration > 0:
            active_subscriptions['combo'] = (combo_type, len(combo_list))
        
        result = {
            'month_price': month_price,
            'total_devices': total_devices,
            'devices_list': all_list,
            'durations': durations,
            'is_subscribed': is_subscribed,
            'active_subscriptions': active_subscriptions
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to process user info for {user_id}: {e}")
        raise

async def check_slot(user_id: int, device: str) -> str:
    """Determine the appropriate slot (device, router, combo) for adding a device."""
    logger.info(f"Checking slot for user_id={user_id}, device={device}")
    
    # Fetch user info and data
    user_info = await get_user_info(user_id)
    user_data = await get_user_data(user_id)
    
    if user_info is None or user_data is None:
        logger.warning(f"No user data found for user_id={user_id}")
        return 'no_user'

    # Define device types
    DEVICES = ['android', 'iphone/ipad', 'windows', 'macos', 'tv']
    
    # Extract durations
    device_dur, router_dur, combo_dur = user_info.get('durations', (0, 0, 0))
    
    # Check for no subscriptions or incompatible device
    if device_dur == router_dur == combo_dur == 0:
        logger.info(f"No active subscriptions for user_id={user_id}")
        return 'no_subscription'
    if router_dur == combo_dur == 0 and device == 'router':
        logger.info(f"No router or combo subscription for router device, user_id={user_id}")
        return 'no_subscription'
    if device_dur == combo_dur == 0 and device in DEVICES:
        logger.info(f"No device or combo subscription for device {device}, user_id={user_id}")
        return 'no_subscription'
    
    # Check combo subscription
    if combo_dur > 0:
        combo_size = user_data['subscription']['combo']['type']
        combo_devices = len(user_data['subscription']['combo']['devices'])
        is_full = combo_devices >= combo_size
        logger.info(f"Combo subscription: size={combo_size}, devices={combo_devices}, is_full={is_full}")
        
        if not is_full:
            logger.info(f"Adding to combo slot for user_id={user_id}")
            return 'combo'
        elif device in DEVICES and device_dur > 0:
            logger.info(f"Combo full, adding to device slot for user_id={user_id}")
            return 'device'
        elif device == 'router' and router_dur > 0:
            logger.info(f"Combo full, adding to router slot for user_id={user_id}")
            return 'router'
        else:
            logger.info(f"Combo full and no suitable subscription for user_id={user_id}")
            return 'no_subscription'
    
    # Check device subscription
    if device_dur > 0 and device in DEVICES:
        logger.info(f"Adding to device slot for user_id={user_id}")
        return 'device'
    
    # Check router subscription
    if router_dur > 0 and device == 'router':
        logger.info(f"Adding to router slot for user_id={user_id}")
        return 'router'
    
    # Fallback error case
    logger.error(f"Unable to determine slot for user_id={user_id}, device={device}")
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

# POLLING OF CRYPTOBOT PAYMENT
active_invoices: Dict[str, dict] = {}

async def poll_invoices(bot: Bot):
    while True:
        try:
            invoices = await payment_req.get_active_invoices()
            for invoice in invoices:
                invoice_id = invoice["invoice_id"]
                user_id = invoice["user_id"]
                default_amount = invoice["amount"]
                default_payload = f"{user_id}:{default_amount}:0:balance:balance:add_balance:balance"
                payload = invoice.get("payload", default_payload)
                _, amount, period, device_type, device, payment_type, method = payload.split(':')
        
                invoice_status = await payment_req.check_invoice_status(invoice_id)
                if invoice_status:
                    status = invoice_status["status"]
                    if status == "paid":
                        logger.info(f"Invoice {invoice_id} paid for user {user_id}")
                        try:
                            balance_response = await payment_req.payment_balance_process(
                                user_id=user_id,
                                amount=amount,
                                period=period,
                                device_type=device_type,
                                device=device,
                                payment_type=payment_type,
                                method=method
                            )
                            if balance_response:
                                await bot.send_message(user_id, text="Оплата успешна 🎉")
                                await payment_req.update_invoice_status(invoice_id, "completed")
                        except Exception as e:
                            logger.error(f"Error processing payment for invoice {invoice_id}: {e}")
                    elif status in ["expired", "failed"]:
                        logger.info(f"Invoice {invoice_id} {status}, updating status")
                        await payment_req.update_invoice_status(invoice_id, status)
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            await asyncio.sleep(30)

async def start_polling_invoice(
    invoice_id: str, user_id: int, amount: float, period: int,
    device_type: str, device: str, payment_type: str
):
    active_invoices[invoice_id] = {
        "user_id": user_id,
        "amount": amount,
        "period": period,
        "device_type": device_type,
        "device": device,
        "payment_type": payment_type
    }

async def on_startup(bot: Bot):
    logger.info("Starting invoice polling")
    asyncio.create_task(poll_invoices(bot))



