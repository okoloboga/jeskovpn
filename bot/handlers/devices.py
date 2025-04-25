import logging
from typing import Union
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from fluentogram import TranslatorRunner

from services import services, vpn_req, PaymentSG
from keyboards import payment_kb, devices_kb, main_kb, another_kb

devices_router = Router()

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s'
)

@devices_router.message(F.text.in_(["Мои устройства 📱", "My Devices 📱"]))
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
        user_info = await services.user_info(user_id)
        if user_data is None or user_info is None:
            text = i18n.error.user_not_found()
            if isinstance(event, CallbackQuery):
                await event.message.edit_text(text=text)
                await event.answer()
            else:
                await event.answer(text=text)
            return

        devices = user_data["subscription"]["device"]["devices"]
        combo_cells = user_data["subscription"]["combo"]["devices"]

        count_devices = user_info['total_devices']
        subscription_fee = user_info['day_price']
        keyboard = devices_kb.my_devices_kb(i18n, devices, combo_cells)
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
    logger.info(f"User {user_id} selected a device")

    try:
        _, _, device = callback.data.split("_")
        device_key = await vpn_req.get_device_key(user_id, device)
        if device_key is None:
            await callback.message.edit_text(text=i18n.error.device_key_not_found())
            await callback.answer()
            return

        keyboard = devices_kb.device_kb(i18n, device)
        text = i18n.device.menu(device=device, device_key=device_key)
        await callback.message.edit_text(text=text, reply_markup=keyboard)
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
@devices_router.callback_query(F.data == "add_device")
async def connect_vpn_handler(
    event: Union[CallbackQuery, Message],
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
    user_id = event.from_user.id
    logger.info(f"User {user_id} wants to add a device")

    try:
        user_info = await services.user_info(user_id)
        day_price = user_info['day_price']
        subscription_fee = int(day_price * 30)
        devices = user_info['total_devices']
        devices_list = user_info['devices_list']

        if isinstance(event, CallbackQuery):
            await event.message.answer(text=i18n.devices.menu(
                                                devices=devices,
                                                subscription_fee=subscription_fee), 
                                       reply_markup=devices_kb.add_device_kb(i18n))
            await event.answer()
        else:
            await event.answer(text=i18n.devices.menu(
                                    devices=devices,
                                    subscription_fee=subscription_fee), 
                               reply_markup=devices_kb.add_device_kb(i18n))

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

@devices_router.message(F.text.in_(["Устройство", "Device", "Комбо набор", "Combo Package"]))
async def select_device_type(
    message: Message,
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
    user_id = message.from_user.id
    device_type = message.text.lower()
    await state.clear()
    logger.info(f"User {user_id} selected device type: {device_type}")

    try:
        device_type = "device" if ("device" == device_type or "устройство" == device_type) else "combo"
        await state.update_data(device_type=device_type)
        keyboard = devices_kb.devices_list_kb(i18n, device_type)
        await message.answer(text=i18n.devices.category.menu(), reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@devices_router.message(F.text.in_(["Android 🤖", "iPhone/iPad 📱", "Windows 💻", "MacOS 🍎", "TV 📺", "Роутер 🌐", "Router 🌐"]))
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
    device, _ = message.text.lower().split(' ')
    logger.info(f"User {user_id} selected device: {device}")

    try:
        user_data = await services.get_user_data(user_id)
        user_info = await services.user_info(user_id)
        if user_data is None or user_info is None:
            await message.answer(text=i18n.error.user_not_found())
            return
        else:
            day_price = user_info['day_price']
            balance = user_data['balance']
            is_subscribed = False if day_price == 0 else False

        await state.update_data(
            device=device,
            balance=balance,
            days = 0 if day_price == 0 else int(balance/day_price),
            is_subscribed=is_subscribed
        )
        keyboard = devices_kb.period_select_kb(i18n)
        if device != 'router' or device != 'роутер':
            text = i18n.period.menu(
                balance=balance,
                days = 0 if day_price == 0 else int(balance/day_price)
            )
        else: 
            text = i18n.period.menu.router(
                balance=balance,
                days = 0 if day_price == 0 else int(balance/day_price)
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
    combo_type = "combo_10" if message.text[0] == "1" else "combo_5"
    logger.info(f"User {user_id} selected combo: {combo_type}")

    try:
        user_data = await services.get_user_data(user_id)
        user_info = await services.user_info(user_id)
        if user_data is None or user_info is None:
            await message.answer(text=i18n.error.user_not_found())
            return
        else:
            day_price = user_info['day_price']
            balance = user_data['balance']
            is_subscribed = False if day_price == 0 else False

        await state.update_data(
            device=combo_type,
            balance=balance,
            days = 0 if day_price == 0 else int(balance/day_price),
            is_subscribed=is_subscribed
        )
        keyboard = devices_kb.period_select_kb(i18n)
        if combo_type == "combo5":
            text = i18n.period.menu.combo5(
                balance=balance,
                days = 0 if day_price == 0 else int(balance/day_price)
            )
        else: 
            text = i18n.period.menu.combo10(
                balance=balance,
                days = 0 if day_price == 0 else int(balance/day_price)
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
        user_info = await services.user_info(user_id)
        state_data = await state.get_data()
        balance = state_data['balance']
        device = state_data['device']

        if state_data['device'] in ['android', 'iphone', 'macos', 'windows', 'tv']:
            device = 'device'
        elif state_data['device'] == 'router':
            device = 'router'
        else:
            device = state_data['device']

        _, period = callback.data.split("_")
        payment_type = "buy_subscription"
        await state.set_state(PaymentSG.buy_subscription)
        await state.update_data(period=period, payment_type=payment_type)
    
        if device == 'combo_5' or device == 'combo_10':
            combo, combo_type = device.split('_')
            amount = services.MONTH_PRICE[combo][combo_type][period]
        else:
            amount = services.MONTH_PRICE[device][period]

        day_price = user_info['day_price']
        days = 0 if day_price == 0 else int(balance / day_price)
        keyboard = payment_kb.payment_select(i18n, payment_type)
        text = i18n.payment.menu(
            balance=balance,
            days=days,
            amount=amount
        )
        await callback.message.edit_text(text=text, reply_markup=keyboard)
        await callback.answer()
    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.telegram_failed())
        await callback.answer()
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.unexpected())
        await callback.answer()

@devices_router.message(
        PaymentSG.add_device, 
        F.text.in_(["Android 🤖", "iPhone/iPad 📱", "Windows 💻", "MacOS 🍎", "TV 📺", "Роутер 🌐", "Router 🌐"]))
async def add_device_handler(
    message: Message,
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:

    user_id = message.from_user.id
    user_info = await services.user_info(user_id)
    durations = user_info['durations']
    device, _ = message.text.lower().split(' ')
    device = 'router' if device == 'роутер' else device

    if durations['device'] == durations['router'] == durations['combo'] == 0:
        logger.info(f'User {user_id} hasnt durations: {durations}')
        await message.answer(text=i18n.nosubscription.have.balance,
                             reply_markup=another_kb.subscription_menu(i18n))
        return
    if device == 'router' and durations['router'] == 0:
        logger.info(f'User {user_id} hasnt duration for {device}: {durations}')
        await message.answer(text=i18n.nosubscription.selected_device,
                             reply_markup=another_kb.subscription_menu(i18n))
        return
    elif device
    
    await state.clear()
    logger.info(f"User {user_id} add device: {device}")

    try:
        result = await vpn_req.get_device_key(user_id=user_id, device=device)
        if 'error' not in result:   
            await message.answer(
                    text=i18n.device.menu(device=device, device_key=result),
                    reply_markup=devices_kb.device_kb(i18n=i18n, device=device)
                    )
        else:
            await message.answer(text=i18n.error.unexpected())
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@devices_router.callback_query(F.data.startswith('remove_device_'))
async def remove_device_handler(
        callback: CallbackQuery,
        i18n: TranslatorRunner
) -> None:

    user_id = callback.from_user.id
    user_data = await services.get_user_data(user_id)

    if user_data is None:
        await callback.edit_text(text=i18n.error.user_not_found(),
                                 reply_markup=main_kb.back_inline_kb(i18n))
        return
    _, _, device = callback.data.split('_')    
    devices = user_data["subscription"]["device"]["devices"]
    combo_cells = user_data["subscription"]["combo"]["devices"]

    logger.info(f"User {user_id} removing device {device}")

    try:
        await vpn_req.remove_device_key(user_id, device)
        await callback.message.edit_text(text=i18n.device.removed(device=device),
                                         reply_markup=devices_kb.my_devices_kb(
                                             i18n=i18n,
                                             devices=devices,
                                             combo_cells=combo_cells
                                             )
                                         )
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await callback.answer(text=i18n.error.unexpected())


