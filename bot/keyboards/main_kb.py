from aiogram.types import (ReplyKeyboardBuilder, KeyboardButton, InlineKeyboardBuilder, 
                           InlineKeyboardButton, ReplyKeyboardRemove, WebAppInfo)
     
from fluentogram import TranslatorRunner


def main_kb(i18n: TranslatorRunner, 
            is_subscripted: bool,
            subscription_expires: str,
            balance: str,
            user_language: str):
    
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(i18n.active.sub.button(expires=subscription_expires) if is_subscripted else i18n.inactive.sub.button))
    builder.row(
        KeyboardButton(i18n.balance.button(balace=balance)),
        KeyboardButton(i18n.connect.vpn.button)
    )
    builder.row(KeyboardButton(i18n.devices.button))
    builder.row(
        KeyboardButton(i18n.invite.button),
        KeyboardButton(i18n.support.button)
    )
    builder.row(KeyboardButton("🇷🇺" if user_language == "RU" else "🇺🇸"))

    return builder.as_markup()
