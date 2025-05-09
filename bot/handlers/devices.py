import logging
import unicodedata

from typing import Union
from aiogram import Router, F
from aiogram.utils.markdown import code
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.filters import StateFilter
from fluentogram import TranslatorRunner

from services import services, vpn_req, PaymentSG, DevicesSG
from keyboards import payment_kb, devices_kb, main_kb

devices_router = Router()

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s'
)

@devices_router.message(F.text.in_(["🌐 Мои устройства 📱💻", "My Devices 📱"]))
@devices_router.callback_query(F.data == "devices_menu")
async def devices_button_handler(
    event: Union[CallbackQuery, Message],
    i18n: TranslatorRunner
) -> None:
    """
    Handle requests to display the devices menu.

    Shows a list of user's devices and combo cells, along with the subscription fee.

    Args:
        event (Union[CallbackQuery, Message]): The incoming event (callback or message).
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = event.from_user.id
    logger.info(f"Showing devices menu for user {user_id}")

    try:
        user_data = await services.get_user_data(user_id)
        user_info = await services.get_user_info(user_id)
        if user_data is None or user_info is None:
            text = i18n.error.user_not_found()
            if isinstance(event, CallbackQuery):
                await event.message.edit_text(text=text)
                await event.answer()
            else:
                await event.answer(text=text)
            return
        
        devices_list = user_info.get("devices_list", ([], [], []))
        devices, routers, combo = devices_list
        subscriptions = user_info.get("active_subscriptions", {})
        combo_routers = user_data.get("subscription", {}).get("combo", {}).get("routers", [])
        
        # Create list of empty buttons, if combo is active
        if 'combo' in subscriptions:
            no_combo_router = False if len(combo_routers) > 0 else True
            combo_type, _ = subscriptions.get('combo')
            combo_count = len(combo)
            empty_slots = int(combo_type) - combo_count
            combo = (empty_slots, combo)
        else:
            no_combo_router = False
            combo = (0, [])
        devices = devices + routers
        logger.info(f'devices: {devices}; combo: {combo}; no_combo_router: {no_combo_router}')
        count_devices = user_info.get('total_devices', 0)
        subscription_fee = user_info.get('month_price', 0)
        keyboard = devices_kb.my_devices_kb(i18n, devices, combo, no_combo_router)
        text = i18n.devices.menu(
                devices=count_devices,
                subscription_fee=subscription_fee)

        if isinstance(event, CallbackQuery):
            await event.message.answer(text=text, reply_markup=keyboard)
            await event.answer()
        else:
            await event.answer(text=text, reply_markup=keyboard)

    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text=i18n.error.telegram_failed())
            await event.answer()
        else:
            await event.answer(text=i18n.error.telegram_failed())
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text=i18n.error.unexpected())
            await event.answer()
        else:
            await event.answer(text=i18n.error.unexpected())

@devices_router.callback_query(F.data.startswith("selected_device_"))
async def select_devices_handler(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    """
    Handle selection of a specific device.

    Displays device details and a key for VPN connection.

    Args:
        callback (CallbackQuery): The incoming callback query.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = callback.from_user.id
    device = callback.data[16:]
    await state.update_data(device_name=device)
    logger.info(f"User {user_id} selected a device {device}")

    try:
        device_data = await vpn_req.get_device_key(user_id, device)
        if device_data is None:
            await callback.message.edit_text(text=i18n.error.device_key_not_found())
            await callback.answer()
            return
        vpn_key = device_data.get("key")
        cleaned_key = "".join(c for c in vpn_key if unicodedata.category(c)[0] != "C")
        escaped_key = services.escape_markdown_v2(cleaned_key)
        if not cleaned_key.startswith("ss://"):
            logger.error(f"Invalid VPN key format: {cleaned_key}")
            await callback.answer("Error: Invalid VPN key format")
            return

        device_type = device_data.get("device_type")
        keyboard = devices_kb.device_kb(
                i18n=i18n, 
                device_name=device,
                device_type=device_type
            )
        text = i18n.device.menu(
                name=device, 
                device=device_type
            )
        await callback.message.edit_text(text=text)
        await callback.message.answer(
                text=escaped_key, 
                reply_markup=keyboard, 
                parse_mode="MarkdownV2")
        await callback.answer()

    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.telegram_failed())
        await callback.answer()
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.unexpected())
        await callback.answer()

@devices_router.message(F.text.in_(['Подключить VPN 🚀', 'Connect VPN 🚀']))
async def connect_vpn_handler(
    message: Message, 
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    """
    Handle request to add a new device.

    Shows options for adding a device or combo cell.

    Args:
        callback (CallbackQuery): The incoming callback query.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = message.from_user.id
    try:
        user_info = await services.get_user_info(user_id)
        if user_info is None:
            await message.answer(text=i18n.error.user_not_found())
            return
            
        subscriptions = user_info.get('active_subscriptions', {})
        if 'devices' in subscriptions or 'routers' in subscriptions or 'combo' in subscriptions:
            if 'devices' in subscriptions:
                device_type_kb = "device"
                device_type = 'device'
            elif 'router' in subscriptions:
                device_type_kb = 'router'
                device_type = 'router'
            elif 'combo' in subscriptions:
                device_type_kb = 'device'
                device_type = 'combo'
            else:                 
                await message.answer(text=i18n.error.unexpected())
                return

            await state.update_data(
                    device_type=device_type,
                    device_type_kb=device_type_kb
                    )
        await message.answer(text=i18n.device.type.menu(), 
                           reply_markup=devices_kb.add_device_kb(i18n))
        await state.set_state(PaymentSG.add_device)

    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await message.answer(text=i18n.error.telegram_failed())
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@devices_router.message(F.text.in_(["Устройство", "Device", "Комбо набор", "Combo Package"]))
@devices_router.callback_query(F.data.startswith("add_device"))
async def select_device_type(
    event: Union[CallbackQuery, Message],
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    """
    Handle selection of device type (VPN device or combo).

    Saves the device type to the state and shows available devices.

    Args:
        message (Message): The incoming message with device type.
        state (FSMContext): Finite state machine context for storing data.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = event.from_user.id
    if isinstance(event, Message):
        device_type = event.text.lower()
        device_type = "device" if ("device" == device_type or "устройство" == device_type) else "combo"
        only = 'none'
    else:
        logger.info(f'event message data {event.data}')
        if event.data in ('add_device_device', 'add_device_router'):
            _, _, kb_data = event.data.split('_')
            device_type = kb_data
            only = kb_data
        else:
            device_type = 'device'
            only = 'none'

    await state.update_data(device_type=device_type)
    logger.info(f'DEVICE_TYPE: {device_type}; ONLY: {only}')
    try:
        keyboard = devices_kb.devices_list_kb(i18n, device_type, only)
        if isinstance(event, CallbackQuery):
            await event.message.answer(
                    text=i18n.devices.category.menu(), 
                    reply_markup=keyboard)
            await event.answer()
        else:
            await event.answer(                   
                    text=i18n.devices.category.menu(), 
                    reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        if isinstance(event, CallbackQuery):
            await event.message.answer(text=i18n.error.unexpected())
            await event.answer()
        else:
            await event.answer(text=i18n.error.unexpected())

@devices_router.message(F.text.in_(["Android 📱", "iPhone/iPad 📱", "Windows 💻", "MacOS 💻", "TV 📺", "Роутер 🌐", "Router 🌐"]))
async def select_device_handler(
    message: Message,
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    """
    Handle selection of a specific device.

    Saves device details to the state and prompts for subscription period.

    Args:
        message (Message): The incoming message with device name.
        state (FSMContext): Finite state machine context for storing data.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = message.from_user.id
    current_state = await state.get_state()
    state_data = await state.get_data()
    device_type = state_data.get('device_type')
    user_info = await services.get_user_info(user_id)

    if user_info is None:
        await message.answer(text=i18n.error.user_not_found())
        return

    device, _ = message.text.lower().split(' ')
    device = 'router' if device == 'роутер' else device
    device_type = 'router' if device == 'router' else device_type
    user_slot = await services.check_slot(user_id, device)

    if current_state == PaymentSG.add_device:
        buy_subscription = False
    else:
        buy_subscription = True

    if user_slot == 'no_user':
        await message.answer(text=i18n.error.user_not_found())
        return
    elif user_slot == 'error':
        await message.answer(text=i18n.error.unexpected())
        return
    elif user_slot == 'no_subscription':
        buy_subscription = True
    else:
        buy_subscription = False

    logger.info(f"User {user_id} selected device: {device}; state: {current_state}; user slot: {user_slot}; buy_subscription: {buy_subscription}")

    # IF ADD DEVICE - DONT NEED TO BUY
    if not buy_subscription:
        await state.update_data(device=device)
        logger.info(f"User {user_id} add device: {device} to slot {user_slot}")
    
        try:
            await message.answer(text=i18n.fill.device.name())
            await state.set_state(DevicesSG.device_name)
        except Exception as e:
            logger.error(f"Unexpected error for user {user_id}: {e}")
            await message.answer(text=i18n.error.unexpected())

    # IF NOT ADD DEVICE - WHANT TO BUY        
    else:
        try:
            await state.update_data(device=device)
            user_data = await services.get_user_data(user_id)
            if user_data is None or user_info is None:
                await message.answer(text=i18n.error.user_not_found())
                return
            
            days_left = user_info.get('durations', (0, 0, 0))
            balance = user_data.get('balance', 0)
            is_subscribed = user_info.get('is_subscribed', False)

            await state.update_data(
                device=device,
                balance=balance,
                device_type=device_type,
                days=max(days_left),
                is_subscribed=is_subscribed
            )
            keyboard = devices_kb.period_select_kb(i18n)

            if device == 'router':
                text = i18n.period.menu.router(
                    balance=balance,
                    days=max(days_left)                
                    )
            else: 
                text = i18n.period.menu(
                    balance=balance,
                    days=max(days_left)               
                    )
            await message.answer(text=text, reply_markup=keyboard)
        except Exception as e:
            logger.error(f"Unexpected error for user {user_id}: {e}")
            await message.answer(text=i18n.error.unexpected())

@devices_router.message(F.text.startswith('5 ') | F.text.startswith('10 '))
async def select_combo_handler(
    message: Message,
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    """
    Handle selection of a combo pack.

    Saves device details to the state and prompts for subscription period.

    Args:
        message (Message): The incoming message with device name.
        state (FSMContext): Finite state machine context for storing data.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = message.from_user.id
    current_state = await state.get_state()
    combo_type = "10" if message.text[0] == "1" else "5"
    logger.info(f"User {user_id} selected combo: {combo_type}; current state: {current_state}")

    try:
        user_data = await services.get_user_data(user_id)
        user_info = await services.get_user_info(user_id)
        if user_data is None or user_info is None:
            await message.answer(text=i18n.error.user_not_found())
            return
        days_left = user_info.get('durations', (0, 0, 0))
        balance = user_data.get('balance', 0)
        is_subscribed = user_info.get('is_subscribed', False)

        await state.update_data(
            device=combo_type,
            device_type='combo',
            balance=balance,
            days=max(days_left),
            is_subscribed=is_subscribed
        )
        keyboard = devices_kb.period_select_kb(i18n)
        if combo_type == "5":
            text = i18n.period.menu.combo5(
                balance=balance,
                days=max(days_left)
            )
        else: 
            text = i18n.period.menu.combo10(
                balance=balance,
                days=max(days_left)           
            )
        await message.answer(text=text, reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@devices_router.callback_query(F.data.startswith("month_"))
async def select_period_handler(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    """
    Handle selection of subscription period.

    Saves period and payment type to the state and prompts for payment.

    Args:
        callback (CallbackQuery): The incoming callback query with period.
        state (FSMContext): Finite state machine context for storing data.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = callback.from_user.id
    logger.info(f"User {user_id} selected subscription period")
  
    try:
        user_info = await services.get_user_info(user_id)
        if user_info is None:
            await callback.message.edit_text(text=i18n.error.user_not_found())
            await callback.answer()
            return

        state_data = await state.get_data()
        balance = state_data.get('balance')
        device = state_data.get('device')
        device_type = state_data.get('device_type')

        logger.info(f'device: {device}; device_type: {device_type}')

        if device in ['android', 'iphone/ipad', 'macos', 'windows', 'tv']:
            device_type = 'device'
        elif device == 'router':
            device_type = 'router'
        else:
            device_type = 'combo'

        _, period = callback.data.split("_")
        payment_type = "buy_subscription"
    
        if device == '5' or device == '10':
            combo = 'combo'
            combo_type = device
            amount = services.MONTH_PRICE[combo][combo_type][period]
        else:
            amount = services.MONTH_PRICE[device_type][period]

        logger.info(f'device_type: {device_type}; device: {device}; amount: {amount}')

        days_left = user_info.get('durations', (0, 0, 0))
        keyboard = payment_kb.payment_select(i18n, payment_type)
        text = i18n.buy.subscription.menu(
            balance=balance,
            days=max(days_left),
            amount=amount
        )
        await state.set_state(PaymentSG.buy_subscription)
        await state.update_data(
                amount=amount,
                period=period, 
                payment_type=payment_type,
                device=device,
                device_type=device_type)
        await callback.message.edit_text(text=text, reply_markup=keyboard)
        await callback.answer()

        current_state = await state.get_data()
        current_amount = current_state.get('amount')
        current_device = current_state.get('device')
        logger.info(f"CURRENT AMOUNT {current_amount} CURRENT DEVICE {current_device}")

    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.telegram_failed())
        await callback.answer()
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.unexpected())
        await callback.answer()

@devices_router.message(StateFilter(DevicesSG.device_name))
async def fill_device_name(
        message: Message,
        state: FSMContext,
        i18n: TranslatorRunner
) -> None:

    user_id = message.from_user.id
    device_name = message.text
    validation = services.validate_device_name(device_name)
    state_data = await state.get_data()
    device = state_data.get('device')
    device_type = state_data.get('device_type', 'device')
    logger.info(f'User {user_id} fill device name {device_name}-{device_type} for device {device}; validation: {validation}')

    try:
        user_slot = await services.check_slot(user_id, device)

        if user_slot == 'error':
            await message.answer(text=i18n.error.slot())
            return
        if validation == 'wrong_pattern':
            await message.answer(text=i18n.error.device.name.pattern())
            return
        elif validation == 'wrong_len':
            await message.answer(text=i18n.error.device.name.len())
            return

        result = await vpn_req.generate_device_key(
                        user_id=user_id, 
                        device=device,
                        device_name=device_name,
                        slot=user_slot
                        )
        if result is not None and 'key' in result:
            vpn_key = result.get('key')
            cleaned_key = "".join(c for c in vpn_key if unicodedata.category(c)[0] != "C")
            escaped_key = services.escape_markdown_v2(cleaned_key)
            if not cleaned_key.startswith("ss://"):
                logger.error(f"Invalid VPN key format: {cleaned_key}")
                await message.answer("Error: Invalid VPN key format")
                return

            await message.answer(
                text=i18n.device.menu(
                    name=device_name, 
                    device=device))

            await message.answer(
                    text=escaped_key,                 
                    reply_markup=devices_kb.device_kb(
                        i18n=i18n, 
                        device_name=device_name, 
                        device_type=device),
                    parse_mode="MarkdownV2")
        elif result == 'already_exists':
            await message.answer(text=i18n.device.name.already.exists())
        else:
            await message.answer(text=i18n.error.unexpected())
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@devices_router.message(StateFilter(DevicesSG.rename_device))
async def new_name_handler(
        message: Message,
        state: FSMContext,
        i18n: TranslatorRunner
) -> None:

    user_id = message.from_user.id
    device_new_name = message.text
    validation = services.validate_device_name(device_new_name)
    state_data = await state.get_data()
    device_old_name = state_data.get('device_name')
    logger.info(f'User {user_id} rename device: {device_new_name}; validation: {validation}')

    try:
        if validation == 'wrong_pattern':
            await message.answer(text=i18n.error.device.name.pattern())
            return
        elif validation == 'wrong_len':
            await message.answer(text=i18n.error.device.name.len())
            return
        update_result = await vpn_req.rename_device(user_id, device_old_name, device_new_name)
        device_data = await vpn_req.get_device_key(user_id, device_new_name)
        if update_result is None:
            await message.answer(text=i18n.error.device.rename())
            return
        if device_data is None:
            await message.answer(text=i18n.error.device_key_not_found())
            return
        vpn_key = device_data.get("key")
        
        cleaned_key = "".join(c for c in vpn_key if unicodedata.category(c)[0] != "C")
        escaped_key = services.escape_markdown_v2(cleaned_key)
        if not cleaned_key.startswith("ss://"):
            logger.error(f"Invalid VPN key format: {cleaned_key}")
            await message.answer("Error: Invalid VPN key format")
            return

        device_type = device_data.get("device_type")
        keyboard = devices_kb.device_kb(
                i18n=i18n, 
                device_name=device_new_name,
                device_type=device_type
            )
        text = i18n.device.menu(
                name=device_new_name, 
                device=device_type)
        await message.answer(text=text)
        await message.answer(
                text=escaped_key, 
                reply_markup=keyboard, 
                parse_mode="MarkdownV2")
 
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@devices_router.callback_query(F.data.startswith('rename_device_'))
async def rename_device_handler(
        callback: CallbackQuery,
        state: FSMContext,
        i18n: TranslatorRunner
) -> None:

    user_id = callback.from_user.id
    device = callback.data[14:]
    logger.info(f"User {user_id} rename device {device}")

    await callback.message.edit_text(text=i18n.new.device.name())
    await state.set_state(DevicesSG.rename_device)
   
@devices_router.callback_query(F.data.startswith('remove_device_'))
async def remove_device_handler(
        callback: CallbackQuery,
        i18n: TranslatorRunner
) -> None:

    user_id = callback.from_user.id
    device = callback.data[14:]  
    logger.info(f"User {user_id} removing device {device}")

    try:
        await vpn_req.remove_device_key(user_id, device)
        user_data = await services.get_user_data(user_id)
        user_info = await services.get_user_info(user_id)

        if user_data is None or user_info is None:
            await callback.edit_text(text=i18n.error.user_not_found(),
                                     reply_markup=main_kb.back_inline_kb(i18n))
            return
        devices_list = user_info.get("devices_list", ([], [], []))
        devices, routers, combo = devices_list
        subscriptions = user_info.get("active_subscriptions", {})
        
        # Create list of empty buttons, if combo is active
        if 'combo' in subscriptions:
            combo_type, _ = subscriptions.get('combo')
            combo_count = len(combo)
            empty_slots = int(combo_type) - combo_count
            combo = (empty_slots, combo)
        else:
            combo = (0, [])

        devices = devices + routers

        await callback.message.edit_text(text=i18n.device.removed(device=device),
                                         reply_markup=devices_kb.my_devices_kb(
                                             i18n=i18n,
                                             devices=devices,
                                             combo_cells=combo
                                             )
                                         )
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await callback.answer(text=i18n.error.unexpected())

@devices_router.callback_query(F.data == 'instruction')
async def instruction_handler(
        callback: CallbackQuery,
        i18n: TranslatorRunner
) -> None:

    await callback.message.answer(text=i18n.instruction.android())
