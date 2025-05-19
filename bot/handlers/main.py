import logging
from typing import Union
from aiogram import Router, F
from aiogram.utils.deep_linking import decode_payload
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery, Message
from fluentogram import TranslatorRunner

from services import user_req, services
from keyboards import main_kb

main_router = Router()

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s'
)

@main_router.message(CommandStart(deep_link_encoded=True))
async def command_start_getter(
    message: Message,
    i18n: TranslatorRunner,
    state: FSMContext,
    command: Command
) -> None:
    """
    Handle the /start command, including referral deep links.

    Creates a new user if not exists, processes referrals, and shows the main menu.

    Args:
        message (Message): The incoming message with /start command.
        i18n (TranslatorRunner): Translator for localized responses.
        command (Command): Parsed command object with potential referral payload.

    Returns:
        None
    """
    user_id = message.from_user.id
    first_name = message.from_user.first_name 
    last_name = message.from_user.last_name
    username = message.from_user.username
    await state.clear()

    logger.info(f"Processing /start for user {user_id}, first_name: {first_name}, last_name: {last_name}, username: {username}")
    logger.info(f"Command arguments: {command.args}")

    # Process referral payload
    is_invited = False
    inviter_id = None
    name = first_name if first_name is not None or first_name != '' else username
    if command.args:
        try:
            inviter_id = decode_payload(command.args)
            logger.info(f"Referral payload decoded: {inviter_id}")
        except Exception as e:
            logger.error(f"Failed to decode referral payload: {e}")

    # Check if user exists
    try:
        # logger.info(f"Creating new user {user_id}")
        result = await user_req.create_user(
            user_id=user_id,
            first_name=first_name if first_name is not None else 'no_first_name',
            last_name=last_name if last_name is not None else 'no_last_name',
            username=username if username is not None else 'no_username'
        )
        if result is not None:
            # Add referral if provided
            if inviter_id and inviter_id != str(user_id):
                try:
                    await user_req.add_referral(inviter_id, user_id)
                    is_invited = True
                    logger.info(f"Referral added: {inviter_id} invited {user_id}")
                except Exception as e:
                    logger.error(f"Failed to add referral {inviter_id} for {user_id}: {e}")

        # Fetch user data
        user_data = await services.get_user_data(user_id)
        user_info = await services.get_user_info(user_id)

        # logger.info(f'user_data {user_data}')
        # logger.info(f'user_info {user_info}')

        if user_data is None or user_info is None:
            await message.answer(text=i18n.error.user_not_found())
            return
        else:
            # month_price = user_info.get('month_price', 0)
            balance = user_data.get("balance", 0)
            days_left = user_info.get("durations", (0, 0, 0))
            active_subscriptions = user_info.get('active_subscriptions', {})
            is_subscribed = user_info.get('is_subscribed', False)
        
            # Send welcome message
            head_text = i18n.start.invited.head(name=name, inviter=inviter_id) if is_invited else i18n.start.head.starter(name=name)
            head_text = head_text + "\n"
            if 'devices' in active_subscriptions:
                devices_count = active_subscriptions.get('devices', 0)
                head_text = head_text + f'\n{i18n.active.sub.device(devices_count=devices_count)}'
            if 'routers' in active_subscriptions:
                routers_count = active_subscriptions.get('routers', 0)
                head_text = head_text + f'\n{i18n.active.sub.router(routers_count=routers_count)}'
            if 'combo' in active_subscriptions:
                combo_type, combo_count = active_subscriptions.get('combo', ())
                head_text = head_text + f'\n{i18n.active.sub.combo(combo_type=combo_type, combo_count=combo_count)}'

                
            await message.answer(
                text=head_text,
                reply_markup=main_kb.main_kb(
                    i18n=i18n,
                    is_subscribed=is_subscribed,
                    balance=balance,
                    days_left=max(days_left)
                )
            )
            keyboard_inline = main_kb.connect_vpn_inline_kb(i18n)
            await message.answer(
                text=i18n.start.body(),
                reply_markup=keyboard_inline
                )
    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await message.answer(text=i18n.error.telegram_failed())
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@main_router.message(F.text.in_(["To Main Menu 🏠", "/menu", "В главное меню 🏠"]))
@main_router.callback_query(F.data == "main_menu")
async def main_menu_handler(
    event: Union[CallbackQuery, Message],
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    """
    Handle main menu requests from inline buttons or text commands.

    Displays the main menu with user-specific data.

    Args:
        event (Union[CallbackQuery, Message]): The incoming event (callback or message).
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = event.from_user.id
    first_name = event.from_user.first_name
    username = event.from_user.username
    await state.clear()
    name = first_name if first_name is not None or first_name != '' else username

    logger.info(f"Showing main menu for user {user_id}")

    try:
        # Fetch user data
        user_data = await services.get_user_data(user_id)
        user_info = await services.get_user_info(user_id)

        # logger.info(f'user_data {user_data}')
        # logger.info(f'user_info {user_info}')

        if user_data is None or user_info is None:
            text = i18n.error.user_not_found()
            if isinstance(event, CallbackQuery):
                await event.message.edit_text(text=text)
                await event.answer()
            else:
                await event.answer(text=text)
            return

        # month_price = user_info.get('month_price')
        balance = user_data.get("balance", 0)
        days_left = user_info.get("durations", (0, 0, 0))
        # logger.info(f'days_left: {days_left}; days_left_max: {max(days_left)}')
        active_subscriptions = user_info.get("active_subscriptions", {})
        is_subscribed = user_info.get('is_subscribed', False)
        keyboard=main_kb.main_kb(
            i18n=i18n,
            is_subscribed=is_subscribed,
            balance=balance,
            days_left=max(days_left)
        )

        keyboard_inline=main_kb.connect_vpn_inline_kb(i18n)

        # Send welcome message
        head_text = i18n.start.head(name=name)
        head_text = head_text + "\n"
        if 'devices' in active_subscriptions:
            devices_count = active_subscriptions.get('devices', 0)
            head_text = head_text + f'\n{i18n.active.sub.device(devices_count=devices_count)}'
        if 'routers' in active_subscriptions:
            routers_count = active_subscriptions.get('routers', 0)
            head_text = head_text + f'\n{i18n.active.sub.router(routers_count=routers_count)}'
        if 'combo' in active_subscriptions:
            combo_type, combo_count = active_subscriptions.get('combo', ())
            head_text = head_text + f'\n{i18n.active.sub.combo(combo_type=combo_type, combo_count=combo_count)}'

        # Handle event type
        if isinstance(event, CallbackQuery):
            await event.message.answer(
                text=head_text, reply_markup=keyboard)
            await event.message.answer(
                text=i18n.start.body(), reply_markup=keyboard_inline)
            await event.answer()
        else:
            await event.answer(
                text=head_text, reply_markup=keyboard)
            await event.answer(
                text=i18n.start.body(), reply_markup=keyboard_inline)

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
           
