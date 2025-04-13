import logging
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from fluentogram import TranslatorRunner

logger = logging.getLogger(__name__)

def subscription_menu(i18n: TranslatorRunner) -> ReplyKeyboardMarkup:
    """
    Create a reply keyboard for the subscription menu.

    Offers options to increase balance or return to the main menu.

    Args:
        i18n (TranslatorRunner): Translator for localized button texts.

    Returns:
        ReplyKeyboardMarkup: The subscription menu keyboard.

    Raises:
        KeyError: If localization keys are missing.
    """
    try:
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=i18n.increase.balance.button()),
            KeyboardButton(text=i18n.main.menu.button())
        )
        return builder.as_markup(resize_keyboard=True)
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in subscription_menu: {e}")
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="Main Menu"))
        return builder.as_markup(resize_keyboard=True)
    except Exception as e:
        logger.error(f"Unexpected error in subscription_menu: {e}")
        raise

def reply_keyboard(i18n: TranslatorRunner, user_id: int) -> ReplyKeyboardMarkup:
    """
    Create a reply keyboard for admin responses to support tickets.

    Includes an option to reply to the user.

    Args:
        i18n (TranslatorRunner): Translator for localized button texts.
        user_id (int): Telegram user ID for the ticket.

    Returns:
        ReplyKeyboardMarkup: The admin reply keyboard.

    Raises:
        KeyError: If localization keys are missing.
    """
    try:
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text=i18n.ticket.reply.button(user_id=user_id)))
        return builder.as_markup(resize_keyboard=True)
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in reply_keyboard: {e}")
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="Reply"))
        return builder.as_markup(resize_keyboard=True)
    except Exception as e:
        logger.error(f"Unexpected error in reply_keyboard: {e}")
        raise
