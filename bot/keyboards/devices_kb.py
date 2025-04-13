from aiogram.types import (ReplyKeyboardBuilder, KeyboardButton, InlineKeyboardBuilder, 
                           InlineKeyboardButton, ReplyKeyboardRemove, WebAppInfo)
     
from fluentogram import TranslatorRunner


def devices_kb(i18n: TranslatorRunner, 
               devices: list,
               combo_cells: list):
    
    builder = InlineKeyboardBuilder()

    for device in devices:
        builder.row(InlineKeyboardButton(device, callback_data=f'select_device_{device}'))
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

    device_url_dict = {'device_1': 'url_1',
                       'device_2': 'url_2',
                       'device_3': 'url_3'}

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(i18n.device.instruction.button, url=device_url_dict[device]))
    builder.row(InlineKeyboardButton(i18n.devices.button, callback_data='devices_menu'))
    builder.row(InlineKeyboardButton(i18n.main.menu.button, callback_data='main_menu'))

    return builder.as_markup()


def add_device_kb(i18n: TranslatorRunner):

    builder = ReplyKeyboardBuilder()
    
    builder.row(
        KeyboardButton(i18n.vpn.devices.button),
        KeyboardButton(i18n.vpn.combo.button)
    )
    builder.row(KeyboardButton(i18n.main.menu.button))

    return builder.as_markup()


def devices_list_kb(i18n: TranslatorRunner, device_type: str):

    builder = ReplyKeyboardBuilder()

    if device_type == 'device':
        builder.row(
            KeyboardButton(i18n.android.button),
            KeyboardButton(i18n.iphone.button)
        )
        builder.row(
            KeyboardButton(i18n.windows.button),
            KeyboardButton(i18n.macos.button)
        )
        builder.row(
            KeyboardButton(i18n.tv.button),
            KeyboardButton(i18n.router.button)
        )
        builder.row(KeyboardButton(i18n.main.menu.button))
    
    elif device_type == 'combo':
        builder.row(
            KeyboardButton(i18n.combo.five.button),
            KeyboardButton(i18n.combo.ten.button)
        )
        builder.row(KeyboardButton(i18n.main.menu.button))


    return builder.as_markup()

def period_select_kb(i18n: TranslatorRunner):

    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(i18n.one.month.button, callback_data='month_1'),
        InlineKeyboardButton(i18n.three.month.button, callback_data='month_3')
    )
    builder.row(
        InlineKeyboardButton(i18n.six.month.button, callback_data='month_6'),
        InlineKeyboardButton(i18n.twelve.month.button, callback_data='month_12')
    )
    builder.row(InlineKeyboardBuilder(i18n.back.devices.button, callback_data='add_devices'))

    return builder.as_markup()
