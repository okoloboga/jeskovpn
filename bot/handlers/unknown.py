import logging
from aiogram import Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from fluentogram import TranslatorRunner

unknown_router = Router()

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s:%(lineno)d #%(levelname)-8s "
           "[%(asctime)s] - %(name)s - %(message)s"
)

@unknown_router.message()
async def send_answer(
    message: Message,
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    """
    Handle unknown or unrecognized messages.

    Sends a localized response to the user and clears the FSM state if applicable.

    Args:
        message (Message): The incoming message.
        state (FSMContext): Finite state machine context for clearing state.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = message.from_user.id
    logger.info(f"Received unknown message from user {user_id}: {message.text or 'non-text'}")

    try:
        current_state = await state.get_state()
        if current_state:
            await state.clear()
            logger.debug(f"Cleared FSM state for user {user_id}: {current_state}")

        await message.answer(text=i18n.unknown.message())

    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        # No fallback response to avoid spamming if bot is blocked
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
