import logging
from typing import Union
from aiogram import Router, F
from aiogram.utils.deep_linking import decode_payload
from aiogram.exceptions import TelegramBadRequest
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

    logger.info(f"Processing /start for user {user_id}")

    # Process referral payload
    is_invited = False
    referral_id = None
    name = first_name if first_name is not None or first_name != '' else username
    if command.args:
        try:
            referral_id = decode_payload(command.args)
            logger.info(f"Referral payload decoded: {referral_id}")
        except Exception as e:
            logger.error(f"Failed to decode referral payload: {e}")

    # Check if user exists
    try:
        user = await user_req.get_user(user_id)
        if user is None:
            logger.info(f"Creating new user {user_id}")
            await user_req.create_user(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                username=username
            )
            # Add referral if provided
            if referral_id and referral_id != str(user_id):
                try:
                    await user_req.add_referral(referral_id, user_id)
                    is_invited = True
                    logger.info(f"Referral added: {referral_id} invited {user_id}")
                except Exception as e:
                    logger.error(f"Failed to add referral {referral_id} for {user_id}: {e}")

        # Fetch user data
        user_data = await services.get_user_data(user_id)
        if user_data is None:
            await message.answer(text=i18n.error.user_not_found())
            return

        day_price = await services.day_price(user_id)

        balance = user_data["balance"]
        days_left = 0 if day_price == 0 else int(balance/day_price)
        is_subscribed = False if days_left == 0 else True
        
        # Send welcome message
        text = i18n.start.invited(name=name) if is_invited else i18n.start.default(name=name)
        await message.answer(
            text=text,
            reply_markup=main_kb.main_kb(
                i18n=i18n,
                is_subscribed=is_subscribed,
                balance=balance,
                days_left=days_left
            )
        )
    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await message.answer(text=i18n.error.telegram_failed())
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@main_router.message(F.text.in_(["Main Menu", "/menu", "В главное меню"]))
@main_router.callback_query(F.data == "main_menu")
async def main_menu_handler(
    event: Union[CallbackQuery, Message],
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

    name = first_name if first_name is not None or first_name != '' else username

    logger.info(f"Showing main menu for user {user_id}")

    try:
        # Fetch user data
        user_data = await services.get_user_data(user_id)
        if user_data is None:
            text = i18n.error.user_not_found()
            if isinstance(event, CallbackQuery):
                await event.message.edit_text(text=text)
                await event.answer()
            else:
                await event.answer(text=text)
            return

        day_price = await services.day_price(user_id)
        balance = user_data["balance"]
        days_left = 0 if day_price == 0 else int(balance/day_price)
        is_subscribed = False if days_left == 0 else True

        keyboard=main_kb.main_kb(
            i18n=i18n,
            is_subscribed=is_subscribed,
            balance=balance,
            days_left=days_left
        )

        # Handle event type
        if isinstance(event, CallbackQuery):
            await event.message.answer(
                text=i18n.start.default(name=name),
                reply_markup=keyboard
            )
            await event.answer()
        else:
            await event.answer(
                text=i18n.start.default(name=name),
                reply_markup=keyboard
            )
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
           
