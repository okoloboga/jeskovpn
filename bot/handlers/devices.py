import logging
from typing import Union
from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from fluentogram import TranslatorRunner

from services import services, vpn_req
from keyboards import payment_kb, devices_kb, main_kb

devices_router = Router()

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s'
)

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
        user_data = await services.get_user_data(user_id)
        if user_data is None:
            text = i18n.error.user_not_found()
            if isinstance(event, CallbackQuery):
                await event.message.edit_text(text=text)
                await event.answer()
            else:
                await event.answer(text=text)
            return

        devices = user_data["subscription"]["device"]["devices"]
        combo_cells = user_data["subscription"]["combo"]["devices"]
        count_devices = await services.count_devices(user_id)
        subscription_fee = await services.day_price(user_id)
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

@devices_router.message(F.text.in_(['Подключить VPN', 'Connect VPN']))
@devices_router.callback_query(F.data == "add_device")
async def add_device_handler(
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
        day_price = await services.day_price(user_id)
        subscription_fee = int(day_price * 30)
        devices = await services.count_devices(user_id)
        devices_list = await services.user_devices(user_id)

        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text=i18n.devices.menu(
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
        device_type = "device" if ("device" == device_type or "устройство" == device_type) else "combo"
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
        user_data = await services.get_user_data(user_id)
        if user_data is None:
            await message.answer(text=i18n.error.user_not_found())
            return
        else:
            day_price = await services.day_price(user_id)
            balance = user_data['balance']
            is_subscribed = False if day_price == 0 else False

        await state.update_data(
            device=device,
            balance=balance,
            days=int(balance/day_price),
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

@devices_router.message(F.text.in_(['5 устройств + роутер', '10 устройств + роутер', '5 devices + router', '10 devices + router']))
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
    combo_type = "10" if message.text[0] == "1" else "5"
    logger.info(f"User {user_id} selected combo: {combo_type}")

    try:
        user_data = await services.get_user_data(user_id)
        if user_data is None:
            await message.answer(text=i18n.error.user_not_found())
            return
        else:
            day_price = await services.day_price(user_id)
            balance = user_data['balance']
            is_subscribed = False if day_price == 0 else False

        await state.update_data(
            device=device,
            balance=balance,
            days=int(balance/day_price),
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
        balance = state_data['balance']
        day_price = await services.day_price(user_id)
        days = 0 if day_price == 0 else int(balance / day_price)
        keyboard = payment_kb.payment_select(i18n, payment_type)

        text = i18n.payment.menu(
            balance=balance,
            days = days,
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

@devices_router.message(F.text.startswith("# "))
async def manage_device_handler(
    message: Message,
    i18n: TranslatorRunner
) -> None:

    user_id = message.from_user.id
    device = message.text[2:]
    device_key = await vpn_req.get_device_key(user_id, device)
    logger.info(f"User {user_id} managing device {device}")

    try:
        await message.answer(text=i18n.device.menu(
                                    device=device,
                                    device_key=device_key),
                             reply_markup=devices_kb.device_kb(
                                    i18n=i18n,
                                    device=device)
                             )
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


