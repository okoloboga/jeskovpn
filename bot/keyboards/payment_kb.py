from aiogram.types import (ReplyKeyboardBuilder, KeyboardButton, InlineKeyboardBuilder, 
                           InlineKeyboardButton, ReplyKeyboardRemove, WebAppInfo)
     
from fluentogram import TranslatorRunner


def add_balance_kb(i18n: TranslatorRunner):

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(i18n.add.balance100.button, callback_data='add_balance_100'),
        InlineKeyboardButton(i18n.add.balance200.button, callback_data='add_balance_200'),
        InlineKeyboardButton(i18n.add.balance300.button, callback_data='add_balance_300')
    )
    builder.row(
        InlineKeyboardButton(i18n.add.balance400.button, callback_data='add_balance_400'),
        InlineKeyboardButton(i18n.add.balance500.button, callback_data='add_balance_500'),
        InlineKeyboardButton(i18n.add.balance650.button, callback_data='add_balance_650')
    )
    builder.row(
        InlineKeyboardButton(i18n.add.balance750.button, callback_data='add_balance_750'),
        InlineKeyboardButton(i18n.add.balance900.button, callback_data='add_balance_900'),
        InlineKeyboardButton(i18n.add.balance1000.button, callback_data='add_balance_1000')
    )
    builder.row(
        InlineKeyboardButton(i18n.add.balance2000.button, callback_data='add_balance_2000'),
        InlineKeyboardButton(i18n.add.balance3000.button, callback_data='add_balance_3000')
    )
    builder.row(
        InlineKeyboardButton(i18n.payment.custom.button, callback_data='payment_custom'),
        InlineKeyboardButton(i18n.main.menu.button, callback_data='main_menu')
    )

    return builder.as_markup()


def decline_custom_payment(i18n: TranslatorRunner):

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(i18n.decline.payment.button, callback_data='balance'))
    return builder.as_markup()

