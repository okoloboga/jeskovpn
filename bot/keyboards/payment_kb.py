import logging
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from fluentogram import TranslatorRunner
from config import get_config, Channel
channel = get_config(Channel, "channel")
CHANNEL_ID = channel.id

logger = logging.getLogger(__name__)

def add_balance_kb(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for selecting balance top-up amounts.
    Includes fixed amounts, a custom option, and navigation to the main menu.
    Args:
        i18n (TranslatorRunner): Translator for localized button texts.
    Returns:
        InlineKeyboardMarkup: The balance top-up keyboard.
    Raises:
        KeyError: If localization keys are missing.
    """
    try:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text=i18n.add.balance50.button(), callback_data="add_balance_50"),
            InlineKeyboardButton(text=i18n.add.balance100.button(), callback_data="add_balance_100"),
            InlineKeyboardButton(text=i18n.add.balance200.button(), callback_data="add_balance_200"),
        )
        builder.row(
            InlineKeyboardButton(text=i18n.add.balance300.button(), callback_data="add_balance_300"),
            InlineKeyboardButton(text=i18n.add.balance400.button(), callback_data="add_balance_400"),
            InlineKeyboardButton(text=i18n.add.balance500.button(), callback_data="add_balance_500"),
        )
        builder.row(
            InlineKeyboardButton(text=i18n.add.balance650.button(), callback_data="add_balance_650"),
            InlineKeyboardButton(text=i18n.add.balance750.button(), callback_data="add_balance_750"),
            InlineKeyboardButton(text=i18n.add.balance900.button(), callback_data="add_balance_900"),
        )
        builder.row(
            InlineKeyboardButton(text=i18n.add.balance1000.button(), callback_data="add_balance_1000"),
            InlineKeyboardButton(text=i18n.add.balance2000.button(), callback_data="add_balance_2000"),
            InlineKeyboardButton(text=i18n.add.balance3000.button(), callback_data="add_balance_3000")
        )
        builder.row(
            InlineKeyboardButton(text=i18n.payment.custom.button(), callback_data="add_balance_custom"),
            InlineKeyboardButton(text=i18n.main.menu.button(), callback_data="main_menu")
        )
        return builder.as_markup()
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in add_balance_kb: {e}")
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in add_balance_kb: {e}")
        raise

def decline_custom_payment(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for canceling custom balance input.

    Offers a single button to return to the balance menu.

    Args:
        i18n (TranslatorRunner): Translator for localized button texts.

    Returns:
        InlineKeyboardMarkup: The cancel keyboard.

    Raises:
        KeyError: If localization keys are missing.
    """
    try:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text=i18n.decline.payment.button(), callback_data="balance")
        )
        return builder.as_markup()
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in decline_custom_payment: {e}")
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in decline_custom_payment: {e}")
        raise

def payment_select(i18n: TranslatorRunner, payment_type: str) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for selecting payment methods.

    Includes options for ukassa, crypto, stars, and balance (for subscriptions), plus navigation.

    Args:
        i18n (TranslatorRunner): Translator for localized button texts.
        payment_type (str): Type of payment ("add_balance" or "buy_subscription").

    Returns:
        InlineKeyboardMarkup: The payment method selection keyboard.

    Raises:
        KeyError: If localization keys are missing.
    """
    try:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text=i18n.payment.ukassa.button(), callback_data="payment_ukassa"),
            InlineKeyboardButton(text=i18n.payment.crypto.button(), callback_data="payment_crypto")
        )
        builder.row(
            InlineKeyboardButton(text=i18n.payment.stars.button(), callback_data="payment_stars")
        )
        if payment_type == "buy_subscription":
            builder.row(
                InlineKeyboardButton(text=i18n.payment.balance.button(), callback_data="payment_balance")
            )
        builder.row(
            InlineKeyboardButton(text=i18n.main.menu.button(), callback_data="main_menu")
        )
        return builder.as_markup()
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in payment_select: {e}")
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in payment_select: {e}")
        raise

def contact_select_kb(
        i18n: TranslatorRunner, email: str | None, phone: str | None
) -> InlineKeyboardMarkup:
    
    try:
        builder = InlineKeyboardBuilder()
        callback_email = "add_contact_email" if email is None else "contact_email"
        callback_phone = "add_contact_phone" if phone is None else "contact_phone"
        builder.row(
            InlineKeyboardButton(text=i18n.email.button(), callback_data=callback_email),
            InlineKeyboardButton(text=i18n.phone.button(), callback_data=callback_phone)
        )
        builder.row(
            InlineKeyboardButton(text=i18n.main.menu.button(), callback_data="main_menu")
        )
        return builder.as_markup()
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in payment_select: {e}")
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in payment_select: {e}")
        raise

def get_phone_kb(i18n: TranslatorRunner) -> ReplyKeyboardMarkup:

    try:
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=i18n.phone.button(), request_contact=True),
            KeyboardButton(text=i18n.main.menu.button())
            )
        return builder.as_markup(resize_keyboard=True)
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in payment_select: {e}")
        return ReplyKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in payment_select: {e}")
        raise

def pay_inline(i18n: TranslatorRunner, invoice_url: str) -> InlineKeyboardMarkup:

    try:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text=i18n.pay.button(), url=invoice_url),
            InlineKeyboardButton(text=i18n.main.menu.button(), callback_data="main_menu")
            )
        return builder.as_markup()
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in payment_select: {e}")
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in payment_select: {e}")
        raise
       
def subscribe_channel_kb() -> InlineKeyboardMarkup:
    
    try: 
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="Подписаться на канал", url=f"https://t.me/{CHANNEL_ID.lstrip('@')}"),
            InlineKeyboardButton(text="Проверить подписку", callback_data="check_subscription")
        )
        return builder.as_markup()
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in payment_select: {e}")
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in payment_select: {e}")
        raise


