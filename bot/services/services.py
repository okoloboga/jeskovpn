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

STAR_PRICE = {
    "device": {"0": 0, "1": 55, "3": 130, "6": 230, "12": 330},
    "router": {"0": 0, "1": 250, "3": 600, "6": 1000, "12": 1500},
    "combo": {"0": {"0": 0},
              "5": {"0": 0, "1": 275, "3": 660, "6": 1155, "12": 1650},
              "10": {"0": 0, "1": 465, "3": 1120, "6": 1960, "12": 2800}
        }
    }
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
        routers_list = user['subscription']['router']['devices']
        combo_list = user['subscription']['combo']['devices']
        combo_type = user['subscription']['combo']['type']

        if device_duration == 0 and router_duration == 0 and combo_duration == 0:
            month_price = 0
        else:
            if int(device_duration) != 0:
                devices_price = devices_count * (MONTH_PRICE['device'][str(device_duration)] / int(device_duration))
            else:
                devices_price = 0
            if int(router_duration) != 0:
                router_price = routers_count * (MONTH_PRICE['router'][str(router_duration)] / int(router_duration))
            else:
                router_price = 0
            if int(combo_type) != 0 and int(combo_duration) != 0:
                combo_price = combo_count * (MONTH_PRICE['combo'][str(combo_type)][str(combo_duration)] / int(combo_type) / int(combo_duration))
            else:
                combo_price = 0

            month_price = devices_price + router_price + combo_price

        total_devices = len(devices_list) + len(routers_list) + len(combo_list)
        devices_list = (devices_list, routers_list, combo_list)
        durations = (device_duration, router_duration, combo_duration)

        if int(device_duration) + int(router_duration) + int(combo_duration) == 0:
            is_subscribed = False
        else:
            is_subscribed = True
        
        active_subscriptions: dict = {}
        if int(durations[0]) != 0:
            active_subscriptions['devices'] = len(devices_list)
        elif int(durations[1]) != 0:
            active_subscriptions['routers'] = len(routers_list)
        elif int(durations[2]) != 0:
            active_subscriptions['combo'] = (combo_type, len(combo_list))

        result = {'month_price': month_price,
                  'total_devices': total_devices,
                  'devices_list': devices_list,
                  'durations': durations,
                  'is_subscribed': is_subscribed,
                  'active_subscriptions': active_subscriptions}

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
    durations = user_info.get('durations', (0, 0, 0))
    device_dur, router_dur, combo_dur = durations

    if (device_dur == router_dur == combo_dur == 0) or (
            router_dur == combo_dur == 0 and device == 'router') or (
                    device_dur == combo_dur == 0 and device in DEVICES):
        return 'no_subscription'

    elif user_info['durations'][2] != 0:
        is_full = len(user_data['subscription']['combo']['devices']) >= user_data['subscription']['combo']['type']
        if is_full and device in DEVICES and device_dur != 0:
            return 'device'
        elif is_full and device == 'router' and router_dur != 0:
            return 'router'
        elif is_full and device_dur == router_dur == 0:
            return 'no_subscription'
        return 'combo'
    elif device_dur != 0 and device in DEVICES:
        return 'device'
    elif router_dur != 0 and device == 'router':
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



