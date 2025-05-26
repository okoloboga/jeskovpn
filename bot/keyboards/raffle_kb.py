from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from fluentogram import TranslatorRunner
import logging

logger = logging.getLogger(__name__)

def raffle_menu_kb(
        raffle_id: int, 
        raffle_type: str, 
        i18n: TranslatorRunner
) -> InlineKeyboardMarkup:
    try:
        builder = InlineKeyboardBuilder()
        if raffle_type == "ticket":
            builder.row(
                InlineKeyboardButton(
                    text=i18n.buy.tickets(),
                    callback_data=f"raffle_buy_tickets_{raffle_id}"
                )
            )
        return builder.as_markup()
    except Exception as e:
        logger.error(f"Error in raffle_menu_kb: {e}")
        return InlineKeyboardMarkup()

def ticket_purchase_kb(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    try:
        builder = InlineKeyboardBuilder()
        
        builder.row(
            InlineKeyboardButton(text=i18n.ticket.count1.button(), callback_data=f"ticket_count_1")
        )
        builder.row(
            InlineKeyboardButton(text=i18n.ticket.count5.button(), callback_data=f"ticket_count_5")
        )
        builder.row(
            InlineKeyboardButton(text=i18n.ticket.count10.button(), callback_data=f"ticket_count_10"),
            )
        builder.row(
            InlineKeyboardButton(
                text=i18n.cancel(),
                callback_data="cancel_purchase"
            )
        )
        return builder.as_markup()
    except Exception as e:
        logger.error(f"Error in ticket_purchase_kb: {e}")
        return InlineKeyboardMarkup()
