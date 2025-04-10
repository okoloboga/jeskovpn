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


def devices_kb(i18n: TranslatorRunner, 
               devices: list,
               combo_cells: list):
    
    builder = InlineKeyboardBuilder()

    for device in devices:
        builder.row(InlineKeyboardBuilder(device, callback_data=f'select_device_{device}'))
    # COMBO CELL?
    for combo_cell in combo_cells:
        builder.row(InlineKeyboardButton(combo_cell, callback_data=f'select_cell_{combo_cell}'))
    builder.row(
        InlineKeyboardButton(i18n.add.device.button, callback_data='add_device'),
        InlineKeyboardButton(i18n.remove.device.button, callback_data='remove_device')
    )
    builder.row(InlineKeyboardButton(i18n.main.menu.button, callback_data='main_menu'))

    return builder.as_markup()


def device_kb(i18n: TranslatorRunner, device: str):

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(i18n.device.instruction.button, callback_data=f'device_instruction_${device}'))
    builder.row(InlineKeyboardButton(i18n.devices.button, callback_data='devices_menu'))
    builder.row(InlineKeyboardButton(i18n.main.menu.button, callback_data='main_menu'))

    return builder.as_markup()