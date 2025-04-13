 import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner

logger = logging.getLogger(__name__)

def cancel_reply_kb(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for canceling ticket reply.

    Offers a single button to cancel the action.

    Args:
        i18n (TranslatorRunner): Translator for localized button texts.

    Returns:
        InlineKeyboardMarkup: The cancel reply keyboard.

    Raises:
        KeyError: If localization keys are missing.
    """
    try:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=i18n.cancel.button(),
                callback_data="cancel_reply"
            )
        )
        return builder.as_markup()
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in cancel_reply_kb: {e}")
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in cancel_reply_kb: {e}")
        raise

def admin_menu_kb(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for the admin menu.

    Offers navigation to the main admin functions (placeholder).

    Args:
        i18n (TranslatorRunner): Translator for localized button texts.

    Returns:
        InlineKeyboardMarkup: The admin menu keyboard.

    Raises:
        KeyError: If localization keys are missing.
    """
    try:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=i18n.admin.menu.button(),
                callback_data="admin_menu"
            )
        )
        return builder.as_markup()
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in admin_menu_kb: {e}")
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in admin_menu_kb: {e}")
        raise      
