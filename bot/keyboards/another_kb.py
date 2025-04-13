from aiogram.types import (ReplyKeyboardBuilder, KeyboardButton, InlineKeyboardBuilder, 
                           InlineKeyboardButton, ReplyKeyboardRemove, WebAppInfo)
     
from fluentogram import TranslatorRunner


def subscription_menu(i18n: TranslatorRunner):

    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(i18n.increase.balance.button),
        KeyboardButton(i18n.main.menu.button)
    )
    return builder.as_markup()


