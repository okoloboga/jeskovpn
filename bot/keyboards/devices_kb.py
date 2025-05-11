import logging
from typing import List, Tuple, Optional
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from fluentogram import TranslatorRunner

logger = logging.getLogger(__name__)

def my_devices_kb(
    i18n: TranslatorRunner,
    devices: List[str],
    combo_cells: Tuple[int, List[str]],
    no_combo_router: Optional[bool] = False
) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for the devices menu.

    Displays a list of devices and combo cells, with options to add or remove devices.

    Args:
        i18n (TranslatorRunner): Translator for localized button texts.
        devices (List[str]): List of user's devices.
        combo_cells (List[str]): List of user's combo cells.
    
    Returns:
        InlineKeyboardMarkup: The devices menu keyboard.
    
    Raises:
        KeyError: If localization keys are missing.
    """
    try:
        builder = InlineKeyboardBuilder()
        empty_slots, combo_devices = combo_cells
        for device in devices:
            builder.row(InlineKeyboardButton(text=device, callback_data=f"selected_device_{device}"))
        if empty_slots != 0:
            for device in combo_devices:
                builder.row(InlineKeyboardButton(text=device, callback_data=f"selected_device_{device}"))
            for _ in range(empty_slots):
                builder.row(InlineKeyboardButton(text=i18n.add.device.button(), callback_data=f"add_device_device"))
        else:
            builder.row(
                InlineKeyboardButton(text=i18n.add.device.button(), callback_data="add_device"),
            )
        if no_combo_router:
            builder.row(InlineKeyboardButton(text=i18n.add.router.button(), callback_data=f"add_device_router"))            
        builder.row(
            InlineKeyboardButton(text=i18n.main.menu.button(), callback_data="main_menu"),
            InlineKeyboardButton(text=i18n.device.instruction.button(), callback_data="select_instruction")
            )
        return builder.as_markup()
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in devices_kb: {e}")
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in devices_kb: {e}")
        raise

def device_kb(i18n: TranslatorRunner, device_name: str, device_type: str) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for a specific device.

    Provides a link to instructions and navigation buttons.

    Args:
        i18n (TranslatorRunner): Translator for localized button texts.
        device (str): The selected device name.

    Returns:
        InlineKeyboardMarkup: The device-specific keyboard.

    Raises:
        KeyError: If localization keys are missing.
    """
    try:
        builder = InlineKeyboardBuilder()
        builder.row(
                InlineKeyboardButton(text=i18n.rename.device.button(), callback_data=f"rename_device_{device_name}")
                )
        builder.row(
                InlineKeyboardButton(text=i18n.device.instruction.button(), callback_data="instruction"),
                InlineKeyboardButton(text=i18n.remove.device.button(), callback_data=f"remove_device_{device_name}")
                )
        builder.row(InlineKeyboardButton(text=i18n.devices.button(), callback_data="devices_menu"))
        builder.row(InlineKeyboardButton(text=i18n.main.menu.button(), callback_data="main_menu"))
        return builder.as_markup()
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in device_kb: {e}")
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in device_kb: {e}")
        raise

def add_device_kb(i18n: TranslatorRunner) -> ReplyKeyboardMarkup:
    """
    Create a reply keyboard for selecting device type to add.

    Offers options for VPN devices or combo cells.

    Args:
        i18n (TranslatorRunner): Translator for localized button texts.

    Returns:
        ReplyKeyboardMarkup: The device type selection keyboard.

    Raises:
        KeyError: If localization keys are missing.
    """
    try:
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text=i18n.vpn.devices.button()),
            KeyboardButton(text=i18n.vpn.combo.button())
        )
        builder.row(KeyboardButton(text=i18n.main.menu.button()))
        return builder.as_markup(resize_keyboard=True)
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in add_device_kb: {e}")
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="Back"))
        builder.as_markup(resize_keyboard=True)
    except Exception as e:
        logger.error(f"Unexpected error in add_device_kb: {e}")
        raise

def devices_list_kb(i18n: TranslatorRunner, device_type: str, only: str = 'none') -> ReplyKeyboardMarkup:
    """
    Create a reply keyboard for selecting a specific device or combo cell.

    Displays devices or combo cells based on the selected type.

    Args:
        i18n (TranslatorRunner): Translator for localized button texts.
        device_type (str): Type of selection ("device" or "combo").

    Returns:
        ReplyKeyboardMarkup: The device or combo selection keyboard.

    Raises:
        KeyError: If localization keys are missing.
    """
    try:
        builder = ReplyKeyboardBuilder()
        if device_type.lower() == "device" or device_type.lower() == 'router':
            if only == 'none':
                builder.row(
                    KeyboardButton(text=i18n.device.android.button()),
                    KeyboardButton(text=i18n.device.iphone.button())
                )
                builder.row(
                    KeyboardButton(text=i18n.device.windows.button()),
                    KeyboardButton(text=i18n.device.macos.button())
                )
                builder.row(
                    KeyboardButton(text=i18n.device.tv.button()),

                    KeyboardButton(text=i18n.device.router.button())
                )
            elif only == "device":
                builder.row(
                    KeyboardButton(text=i18n.device.android.button()),
                    KeyboardButton(text=i18n.device.iphone.button())
                )
                builder.row(
                    KeyboardButton(text=i18n.device.windows.button()),
                    KeyboardButton(text=i18n.device.macos.button())
                )
                builder.row(
                    KeyboardButton(text=i18n.device.tv.button())
                )
            elif only == "router":
                builder.row(KeyboardButton(text=i18n.device.router.button()))
        else:
            builder.row(
                KeyboardButton(text=i18n.combo.five.button()),
                KeyboardButton(text=i18n.combo.ten.button())
            )
        builder.row(KeyboardButton(text=i18n.main.menu.button()))
        return builder.as_markup(resize_keyboard=True)
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in devices_list_kb: {e}")
        builder = ReplyKeyboardBuilder()
        builder.row(KeyboardButton(text="Back"))
        return builder.as_markup(resize_keyboard=True)
    except Exception as e:
        logger.error(f"Unexpected error in devices_list_kb: {e}")
        raise

def period_select_kb(i18n: TranslatorRunner) -> InlineKeyboardMarkup:
    """
    Create an inline keyboard for selecting subscription period.

    Offers options for 1, 3, 6, or 12 months.

    Args:
        i18n (TranslatorRunner): Translator for localized button texts.

    Returns:
        InlineKeyboardMarkup: The period selection keyboard.

    Raises:
        KeyError: If localization keys are missing.
    """
    try:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text=i18n.one.month.button(), callback_data="month_1"),
            InlineKeyboardButton(text=i18n.three.month.button(), callback_data="month_3")
        )
        builder.row(
            InlineKeyboardButton(text=i18n.six.month.button(), callback_data="month_6"),
            InlineKeyboardButton(text=i18n.twelve.month.button(), callback_data="month_12")
        )
        builder.row(InlineKeyboardButton(text=i18n.back.devices.button(), callback_data="add_device"))
        return builder.as_markup()
    except (KeyError, AttributeError) as e:
        logger.error(f"Localization error in period_select_kb: {e}")
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in period_select_kb: {e}")
        raise
