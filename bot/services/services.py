import logging
import re
import asyncio
import time

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta, timezone
from dateutil.parser import isoparse
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
INSTUCTIONS_TEMP = {
               'android': "https://play.google.com/store/apps/details?id=org.outline.android.client&hl=en",
               'tv': "https://play.google.com/store/apps/details?id=org.outline.android.client&hl=en",
               'iphone/ipad': "https://apps.apple.com/us/app/outline-app/id1356177741",
               'windows': "https://getoutline.org/get-started/#step-3",
               'macos': "https://getoutline.org/get-started/#step-3",
               'router': "В разработке"
               }
INSTUCTIONS = {
        'android': 'В разработке',
        'tv': 'В разработке',
        'iphone/ipad': 'В разработке',
        'windows': 'В разработке',
        'macos': 'В разработке',
        'router': 'В разработке',
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
        
        # Form subscription in updated format
        subscription = {
            "device": {"devices": {}, "duration": 0},
            "router": {"devices": {}, "duration": 0},
            "combo": {"devices": {}, "routers": {}, "duration": 0, "type": 0}
        }
        
        # Populate devices
        for device in devices["device"]:
            subscription["device"]["devices"][device["device_name"]] = device["device_type"]
        for router in devices["router"]:
            subscription["device"]["devices"][router["device_name"]] = router["device_type"]
       
        # Populate combo devices and routers based on device_type
        combo_sub = next((sub for sub in subscriptions if sub["type"] == "combo"), None)
        if combo_sub and "device_type" in combo_sub:
            for device in devices["combo"]:
                if device["device_type"] == "router":
                    subscription["combo"]["routers"][device["device_name"]] = device["device_type"]
                else:
                    subscription["combo"]["devices"][device["device_name"]] = device["device_type"]
        else:
            pass
            # Fallback: treat all combo devices as non-routers
            # subscription["combo"]["devices"][device["device_name"]] = device["device_type"]

        # logger.info(f'GET subscriptions: {subscriptions}')
        # logger.info(f'GET devices: {devices}')

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
    
    # logger.info(f'USER: {user}')
    
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
        combo_routers = user['subscription']['combo']['routers']
        combo_list.update(combo_routers)

        # Get monthly price from subscriptions
        subscriptions = await payment_req.get_subscriptions(user_id) or []

        # logger.info(f'combo_routers: {combo_routers}; combo_list: {combo_list}')

        month_price = 0.0
        for sub in subscriptions:
            month_price += float(sub["monthly_price"])
        
        devices_len = len(devices_list) if devices_list is not None else 0
        routers_len = len(routers_list) if routers_list is not None else 0
        combo_len = len(combo_list) if combo_list is not None else 0
        total_devices = devices_len + routers_len + combo_len
        durations = (device_duration, router_duration, combo_duration)
        all_list = {"devices": {**devices_list}, "routers": {**routers_list}, "combo": {**combo_list}}
        logger.info(all_list)
        
        is_subscribed = device_duration + router_duration + combo_duration > 0
        
        active_subscriptions: Dict = {}
        if device_duration > 0:
            active_subscriptions['devices'] = devices_len
        if router_duration > 0:
            active_subscriptions['routers'] = routers_len
        if combo_duration > 0:
            active_subscriptions['combo'] = (combo_type, combo_len)

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
        combo_devices = len(user_data['subscription']['combo']['devices']) + len(user_data['subscription']['combo']['routers'])
        is_full = combo_devices >= (combo_size + 1)
        has_router = len(user_data['subscription']['combo']['routers']) > 0
        
        # logger.info(f"Combo subscription: size={combo_size}, devices={combo_devices}, is_full={is_full}, has_router={has_router}")
        
        # Skip combo if adding a router and a router already exists
        if not (device == 'router' and has_router) and not is_full:
            logger.info(f"Adding to combo slot for user_id={user_id}")
            return 'combo'
    
    # Fetch subscriptions to check for free slots
    subscriptions = await payment_req.get_subscriptions(user_id) or []
    device_subscriptions = sum(1 for sub in subscriptions if sub['type'] == 'device' and sub['remaining_days'] > 0)
    router_subscriptions = sum(1 for sub in subscriptions if sub['type'] == 'router' and sub['remaining_days'] > 0)
    
    # Get number of devices
    device_count = len(user_data['subscription']['device']['devices'])
    router_count = len(user_data['subscription']['router']['devices'])
    
    # logger.info(f"Device subscriptions: {device_subscriptions}, devices: {device_count}")
    # logger.info(f"Router subscriptions: {router_subscriptions}, routers: {router_count}")

    # Check device subscription
    if device in DEVICES:
        if device_subscriptions > device_count:
            logger.info(f"Free device subscription available, adding to device slot for user_id={user_id}")
            return 'device'
        logger.info(f"No free device subscription for user_id={user_id}")
        return 'no_subscription'
    
    # Check router subscription
    if device == 'router':
        if router_subscriptions > router_count:
            logger.info(f"Free router subscription available, adding to router slot for user_id={user_id}")
            return 'router'
        logger.info(f"No free router subscription for user_id={user_id}")
        return 'no_subscription'    

    # If combo is full and no free subscriptions
    if combo_dur > 0 and is_full:
        logger.info(f"Combo full and no free subscriptions for user_id={user_id}")
        return 'no_subscription'
    
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

def escape_markdown_v2(text: str) -> str:
    """
    Escape reserved characters for Telegram MarkdownV2.
    
    Args:
        text: Input text to escape
    
    Returns:
        Escaped text
    """
    reserved_chars = r'([_\*\[\]\(\)~`>\#\+\-=\|\{\}\.!\\])'
    return re.sub(reserved_chars, r'\\\1', text)

async def poll_invoices(bot: Bot):
    """Poll active invoices (ЮKassa and CryptoBot) every 10 seconds, expire after 15 minutes."""
    INVOICE_TIMEOUT = timedelta(minutes=15)  # 15 минут

    while True:
        try:
            active_invoices: List[Dict[str, Any]] = await payment_req.get_active_invoices()
            logger.info(f'Polling {len(active_invoices)} active invoices')
            for invoice in active_invoices:
                invoice_id = invoice["invoice_id"]
                user_id = invoice["user_id"]
                default_amount = invoice["amount"]
                default_payload = f"{user_id}:{default_amount}:0:balance:balance:add_balance:balance"
                payload = invoice.get("payload", default_payload)
                
                try:
                    _, amount, period, device_type, device, payment_type, method = payload.split(':')
                except ValueError:
                    logger.error(f"Invalid payload format for invoice {invoice_id}: {payload}")
                    continue

                # Проверка времени истечения
                created_at = invoice.get("created_at")
                if not created_at:
                    logger.error(f"No created_at for invoice {invoice_id}, skipping timeout check")
                    continue
                
                try:
                    created_at = isoparse(created_at) if isinstance(created_at, str) else created_at
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    if datetime.now(timezone.utc) - created_at > INVOICE_TIMEOUT:
                        logger.info(f"Invoice {invoice_id} expired after 15 minutes")
                        await payment_req.update_invoice_status(invoice_id, "expired")
                        try:
                            await bot.send_message(user_id, text="Ваш инвойс истек. Пожалуйста, создайте новый.")
                            logger.info(f"Notified user {user_id} about expired invoice {invoice_id}")
                        except TelegramAPIError as e:
                            logger.error(f"Failed to notify user {user_id} for expired invoice {invoice_id}: {e}")
                        continue
                except Exception as e:
                    logger.error(f"Error parsing created_at for invoice {invoice_id}: {e}")
                    continue

                # Разделение по методу платежной системы
                if method == "ukassa":
                    status_data = await payment_req.check_ukassa_invoice_status(invoice_id)
                    if status_data:
                        status = status_data["status"]
                        if status == "succeeded" and status_data["paid"]:
                            logger.info(f"ЮKassa invoice {invoice_id} paid for user {user_id}")
                            try:
                                logger.info(f"period: {period}; device_type: {device_type}; device: {device}; "
                                           f"payment_type: {payment_type}; method: {method}")
                                balance_response = await payment_req.payment_balance_process(
                                    user_id=user_id, amount=amount, period=period, device_type=device_type,
                                    device=device, payment_type=payment_type, method=method
                                )
                                if balance_response:
                                    try:
                                        await bot.send_message(user_id, text="Оплата успешна 🎉")
                                        await payment_req.update_invoice_status(invoice_id, "completed")
                                        logger.info(f"ЮKassa invoice {invoice_id} completed, notified user {user_id}")
                                    except TelegramAPIError as e:
                                        logger.error(f"Failed to notify user {user_id} for invoice {invoice_id}: {e}")
                            except Exception as e:
                                logger.error(f"Error processing ЮKassa payment for invoice {invoice_id}: {e}")
                        elif status in ["canceled", "expired", "failed"]:
                            logger.info(f"ЮKassa invoice {invoice_id} {status}, updating status")
                            await payment_req.update_invoice_status(invoice_id, status)
                elif method == "crypto":
                    try:
                        invoice_status = await payment_req.check_invoice_status(invoice_id)
                        # logger.info(f"CryptoBot check for {invoice_id} took {time.time() - start_time:.2f} seconds")
                        if invoice_status:
                            status = invoice_status["status"]
                            if status == "paid":
                                logger.info(f"CryptoBot invoice {invoice_id} paid for user {user_id}")
                                try:
                                    logger.info(f"period: {period}; device_type: {device_type}; device: {device}; "
                                               f"payment_type: {payment_type}; method: {method}")
                                    balance_response = await payment_req.payment_balance_process(
                                        user_id=user_id, amount=amount, period=period, device_type=device_type,
                                        device=device, payment_type=payment_type, method=method
                                    )
                                    if balance_response:
                                        try:
                                            await bot.send_message(user_id, text="Оплата успешна 🎉")
                                            await payment_req.update_invoice_status(invoice_id, "completed")
                                            logger.info(f"CryptoBot invoice {invoice_id} completed, notified user {user_id}")
                                        except TelegramAPIError as e:
                                            logger.error(f"Failed to notify user {user_id} for invoice {invoice_id}: {e}")
                                except Exception as e:
                                    logger.error(f"Error processing CryptoBot payment for invoice {invoice_id}: {e}")
                            elif status in ["expired", "failed"]:
                                logger.info(f"CryptoBot invoice {invoice_id} {status}, updating status")
                                await payment_req.update_invoice_status(invoice_id, status)
                    except Exception as e:
                        if "400" in str(e):
                            logger.debug(f"CryptoBot invoice {invoice_id} not found, likely not a CryptoBot invoice")
                        else:
                            logger.error(f"Error checking CryptoBot invoice {invoice_id}: {e}")
                else:
                    logger.warning(f"Unknown payment method for invoice {invoice_id}: {method}")
                    continue

        except Exception as e:
            logger.error(f"Polling error: {e}")
            await asyncio.sleep(30)
        else:
            await asyncio.sleep(10)

async def on_startup(bot: Bot):
    logger.info("Starting invoice polling")
    asyncio.create_task(poll_invoices(bot), name="poll_invoices")
    logger.info("Both polling tasks started")
