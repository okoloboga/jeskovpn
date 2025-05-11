import logging
from datetime import datetime
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from fluentogram import TranslatorRunner

logger = logging.getLogger(__name__)

def main_kb(
    i18n: TranslatorRunner,
    is_subscribed: bool,
    balance: float,
    days_left: float | int
) -> ReplyKeyboardMarkup:
    """
    Create the main menu keyboard with user-specific options.

    The keyboard includes buttons for subscription status, balance, VPN connection,
    devices, referrals, support, and language selection.

    Args:
        i18n (TranslatorRunner): Translator for localized button texts.
        is_subscribed (bool): Whether the user has an active subscription.
        subscription_expires (str): Subscription expiration date in ISO format.
        balance (int): User's balance in rubles.
        user_language (str): User's preferred language code (e.g., "RU", "EN").

    Returns:
        ReplyKeyboardMarkup: The main menu keyboard.

    Raises:
        ValueError: If input parameters are invalid.
        KeyError: If localization keys are missing.
    """
    try:
        if not isinstance(balance, (int, float)) or balance < 0:
            raise ValueError(f"Invalid balance: {balance}")

        builder = ReplyKeyboardBuilder()
        
        # Subscription button
        if is_subscribed:
            try:
                if days_left > 0:
                    sub_text = i18n.active.sub.button(days=str(days_left))
                else:
                    sub_text = i18n.active.sub.withoutdays.button()
            except ValueError:
                sub_text = i18n.inactive.sub.button()
        else:
            sub_text = i18n.inactive.sub.button()
        builder.row(KeyboardButton(text=sub_text))

        # Balance and VPN connection
        builder.row(
            KeyboardButton(text=i18n.balance.button(balance=balance)),
            KeyboardButton(text=i18n.connect.vpn.button())
        )

        # Devices
        builder.row(KeyboardButton(text=i18n.devices.button()))

        # Invite and support
        builder.row(
            KeyboardButton(text=i18n.invite.button()),
            KeyboardButton(text=i18n.support.button())
        )
 
        return builder.as_markup(resize_keyboard=True)

    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in main_kb: {e}")
        # Fallback keyboard
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="Main Menu"))
        return builder.as_markup(resize_keyboard=True)
    except Exception as e:
        logger.error(f"Unexpected error in main_kb: {e}")
        raise

def connect_vpn_inline_kb(i18n: TranslatorRunner) -> InlineKeyboardMarkup:

    try:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=i18n.connect.vpn.button(),
                callback_data="add_device"
            )
        )
        return builder.as_markup()
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in connect_vpn_inline_kb: {e}")
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in connect_vpn_inlnie_kb: {e}")
        raise

def back_to_devices_inline_kb(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    try:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=i18n.devices.button(),
                callback_data="devices_menu"
            )
        )
        return builder.as_markup()
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in back_inline_kb: {e}")
        # Fallback
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in back_inline_kb: {e}")
        raise

def back_inline_kb(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard with a "Back to Main Menu" button.

    Args:
        i18n (TranslatorRunner): Translator for localized button texts.

    Returns:
        InlineKeyboardMarkup: The inline keyboard with a back button.

    Raises:
        KeyError: If localization keys are missing.
    """
    try:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(
                text=i18n.main.menu.button(),
                callback_data="main_menu"
            )
        )
        return builder.as_markup()
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in back_inline_kb: {e}")
        # Fallback
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in back_inline_kb: {e}")
        raise

def back_kb(i18n: TranslatorRunner) -> ReplyKeyboardMarkup:
    """
    Create a reply keyboard with a "Back to Main Menu" button.

    Args:
        i18n (TranslatorRunner): Translator for localized button texts.

    Returns:
        ReplyKeyboardMarkup: The reply keyboard with a back button.

    Raises:
        KeyError: If localization keys are missing.
    """
    try:
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text=i18n.main.menu.button()))
        return builder.as_markup(resize_keyboard=True)
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in back_kb: {e}")
        # Fallback
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="Back"))
        return builder.as_markup(resize_keyboard=True)
    except Exception as e:
        logger.error(f"Unexpected error in back_kb: {e}")
        raise
