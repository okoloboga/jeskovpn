import logging
from typing import Union, Optional
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from fluentogram import TranslatorRunner

from services import user_req, vpn_req
from keyboards import main_kb, devices_kb

devices_router = Router()

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s'
)

async def get_user_data(user_id: int) -> Optional[dict]:
    """
    Fetch user data from the service.

    Args:
        user_id (int): Telegram user ID.

    Returns:
        Optional[dict]: User data with devices, combo_cells, balance, and subscription status, or None if not found.

    Raises:
        Exception: If the service request fails.
    """
    try:
        user = await user_req.get_user(user_id)
        if user is None:
            logger.warning(f"User {user_id} not found")
            return None
        return {
            "devices": getattr(user, "devices", []),
            "combo_cells": getattr(user, "combo_cells", []),
            "balance": getattr(user, "balance", 0),
            "is_subscribed": getattr(user, "is_subscribed", False)
        }
    except Exception as e:
        logger.error(f"Failed to fetch user {user_id}: {e}")
        raise

@devices_router.message(F.text.in_(["Мои устройства", "My Devices"]))
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
        user_data = await get_user_data(user_id)
        if user_data is None:
            text = i18n.error.user_not_found()
            if isinstance(event, CallbackQuery):
                await event.message.edit_text(text=text)
                await event.answer()
            else:
                await event.answer(text=text)
            return

        devices = user_data["devices"]
        combo_cells = user_data["combo_cells"]
        # Placeholder for subscription fee calculation
        subscription_fee = len(devices) * 100  # Example: 100 rubles per device

        keyboard = devices_kb.devices_kb(i18n, devices, combo_cells)
        text = i18n.devices.menu(subscription_fee=subscription_fee)

        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text=text, reply_markup=keyboard)
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

@devices_router.callback_query(F.data == "add_device")
async def add_device_handler(
    callback: CallbackQuery,
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
    user_id = callback.from_user.id
    logger.info(f"User {user_id} wants to add a device")

    try:
        keyboard = devices_kb.add_device_kb(i18n)
        await callback.message.edit_text(text=i18n.add.device.menu(), reply_markup=keyboard)
        await callback.answer()
    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.telegram_failed())
        await callback.answer()
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.unexpected())
        await callback.answer()

@devices_router.message(F.text.in_(["Устройство", "Device", "Комбо набор", "Combo"]))
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
    logger.info(f"User {user_id} selected device type: {device_type}")

    try:
        # Normalize device type
        device_type = "device" if "device" in device_type else "combo"
        await state.update_data(device_type=device_type)
        keyboard = devices_kb.devices_list_kb(i18n, device_type)
        await message.answer(text=i18n.devices.category.menu(), reply_markup=keyboard)
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@devices_router.message(F.text.in_(["Android", "iPhone/iPad", "Windows", "MacOS", "TV", "Роутер", "Router"]))
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
    device = message.text.lower()
    logger.info(f"User {user_id} selected device: {device}")

    try:
        user_data = await get_user_data(user_id)
        if user_data is None:
            await message.answer(text=i18n.error.user_not_found())
            return

        await state.update_data(
            device=device,
            balance=user_data["balance"],
            is_subscribed=user_data["is_subscribed"]
        )
        keyboard = devices_kb.period_select_kb(i18n)
        if device != 'router':
            text = i18n.period.menu(
                balance=user_data["balance"],
                days=balance / 5,
                is_subscribed=user_data["is_subscribed"]
            )
        else: 
            text = i18n.period.menu.router(
                balance=user_data["balance"],
                days=balance / 12,
                is_subscribed=user_data["is_subscribed"]
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
        _, period = callback.data.split("_")
        payment_type = "buy_subscription"
        await state.update_data(period=period, payment_type=payment_type)
        state_data = await state.get_data()

        keyboard = devices_kb.payment_select(i18n, payment_type)
        text = i18n.payment.menu(
            balance=state_data.get("balance", 0),
            days = balance / 5 if state_data['device'] != 'router' else balance / 7,
            is_subscribed=state_data.get("is_subscribed", False)
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
