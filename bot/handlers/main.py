import logging
from typing import Union, Optional
from aiogram import Router, F
from aiogram.utils.deep_linking import decode_payload
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery, Message
from fluentogram import TranslatorRunner

from services import user_req
from keyboards import main_kb

main_router = Router()

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s'
)

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
            "is_subscribed": user.is_subscribed,
            "subscription_expires": user.subscription_expires,
            "language": user.language,
            "balance": user.balance
        }
    except Exception as e:
        logger.error(f"Failed to fetch user {user_id}: {e}")
        raise

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
        user_data = await get_user_data(user_id)
        if user_data is None:
            await message.answer(text=i18n.error.user_not_found())
            return

        # Send welcome message
        text = i18n.start.invited() if is_invited else i18n.start.default()
        await message.answer(
            text=text,
            reply_markup=main_kb.main_kb(
                i18n=i18n,
                is_subscribed=user_data["is_subscribed"],
                subscription_expires=user_data["subscription_expires"],
                balance=user_data["balance"],
                user_language=user_data["language"]
            )
        )
    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await message.answer(text=i18n.error.telegram_failed())
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@main_router.message(F.text.in_(["Main Menu", "/menu", "Вернуться в меню"]))
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
    logger.info(f"Showing main menu for user {user_id}")

    try:
        # Fetch user data
        user_data = await get_user_data(user_id)
        if user_data is None:
            text = i18n.error.user_not_found()
            if isinstance(event, CallbackQuery):
                await event.message.edit_text(text=text)
                await event.answer()
            else:
                await event.answer(text=text)
            return

        # Prepare menu
        keyboard = main_kb.main_kb(
            i18n=i18n,
            is_subscribed=user_data["is_subscribed"],
            subscription_expires=user_data["subscription_expires"],
            balance=user_data["balance"],
            user_language=user_data["language"]
        )

        # Handle event type
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(
                text=i18n.start.default(),
                reply_markup=keyboard
            )
            await event.answer()
        else:
            await event.answer(
                text=i18n.start.default(),
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
    


    



        
