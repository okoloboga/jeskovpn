import logging
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

logger = logging.getLogger(__name__)

def admin_main_menu_kb() -> ReplyKeyboardMarkup:
    try:
        builder = ReplyKeyboardBuilder()
        builder.row(
            KeyboardButton(text="👤 Пользователи"),
            KeyboardButton(text="🔑 Ключи")
        )
        builder.row(
            KeyboardButton(text="💰 Финансы"),
            KeyboardButton(text="📢 Рассылка")
        )
        builder.row(
            KeyboardButton(text="🛡 Безопасность")
        )
        return builder.as_markup(
            resize_keyboard=True,
            input_field_placeholder="Выберите действие"
        )
    except Exception as e:
        logger.error(f"Unexpected error in admin_main_menu_kb: {e}")
        return ReplyKeyboardMarkup()

def users_list_kb(users, page: int, per_page: int) -> InlineKeyboardMarkup:
    try:
        builder = InlineKeyboardBuilder()
        for user in users:
            builder.row(
                InlineKeyboardButton(
                    text=f"{user['username'] or 'N/A'} (ID: {user['user_id']})",
                    callback_data=f"admin_user_profile_{user['user_id']}"
                )
            )
        
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_users_page_{page-1}")
            )
        nav_buttons.append(
            InlineKeyboardButton(text=f"Стр. {page+1}", callback_data="noop")
        )
        if len(users) == per_page:
            nav_buttons.append(
                InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"admin_users_page_{page+1}")
            )
        
        if nav_buttons:
            builder.row(*nav_buttons)
        
        builder.row(
            InlineKeyboardButton(text="🔙 В меню", callback_data="admin_back_to_main")
        )
        return builder.as_markup()
    except (KeyError, TypeError) as e:
        logger.error(f"Data error in users_list_kb: {e}")
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in users_list_kb: {e}")
        return InlineKeyboardMarkup()

def user_profile_kb(user_id: int, is_blacklisted: bool = False) -> InlineKeyboardMarkup:
    try:
        builder = InlineKeyboardBuilder()
        if is_blacklisted:
            builder.row(
                InlineKeyboardButton(
                    text="🔓 Разблокировать",
                    callback_data=f"admin_unblock_user_{user_id}"
                )
            )
        else:
            builder.row(
                InlineKeyboardButton(
                    text="🚫 Заблокировать",
                    callback_data=f"admin_block_user_{user_id}"
                )
            )
        builder.row(
            InlineKeyboardButton(text="🔙 К списку", callback_data="admin_back_to_users")
        )
        return builder.as_markup()
    except Exception as e:
        logger.error(f"Unexpected error in user_profile_kb: {e}")
        return InlineKeyboardMarkup()

def keys_list_kb(keys, page: int, per_page: int) -> InlineKeyboardMarkup:
    try:
        builder = InlineKeyboardBuilder()
        for key in keys:
            vpn_key = key['outline_key_id']
            status = "Активен" if key['is_active'] else "Неактивен"
            builder.row(
                InlineKeyboardButton(
                    text=f"Ключ: {vpn_key} ({status})",
                    callback_data=f"admin_key_profile_{key['outline_key_id']}"
                )
            )
        
        nav_buttons = []
        if page > 0:
            nav_buttons.append(
                InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_keys_page_{page-1}")
            )
        nav_buttons.append(
            InlineKeyboardButton(text=f"Стр. {page+1}", callback_data="noop")
        )
        if len(keys) == per_page:
            nav_buttons.append(
                InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"admin_keys_page_{page+1}")
            )
        
        if nav_buttons:
            builder.row(*nav_buttons)
        
        builder.row(
            InlineKeyboardButton(text="🔙 В меню", callback_data="admin_back_to_main")
        )
        return builder.as_markup()
    except (KeyError, TypeError) as e:
        logger.error(f"Data error in keys_list_kb: {e}")
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in keys_list_kb: {e}")
        return InlineKeyboardMarkup()

def key_profile_kb(vpn_key: str) -> InlineKeyboardMarkup:
    try:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="📜 История", callback_data=f"admin_key_history_{vpn_key}")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 К списку", callback_data="admin_back_to_keys")
        )
        return builder.as_markup()
    except Exception as e:
        logger.error(f"Unexpected error in key_profile_kb: {e}")
        return InlineKeyboardMarkup()

def finance_menu_kb() -> InlineKeyboardMarkup:
    try:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="🔙 В меню", callback_data="admin_back_to_main")
        )
        return builder.as_markup()
    except Exception as e:
        logger.error(f"Unexpected error in finance_menu_kb: {e}")
        return InlineKeyboardMarkup()

def broadcast_menu_kb() -> InlineKeyboardMarkup:
    try:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_broadcast_cancel")
        )
        return builder.as_markup()
    except Exception as e:
        logger.error(f"Unexpected error in broadcast_menu_kb: {e}")
        return InlineKeyboardMarkup()

def admins_list_kb(admins) -> InlineKeyboardMarkup:
    try:
        builder = InlineKeyboardBuilder()
        for admin in admins:
            builder.row(
                InlineKeyboardButton(
                    text=f"ID: {admin['user_id']} (Добавлен: {admin['added_at']})",
                    callback_data=f"admin_remove_admin_{admin['user_id']}"
                )
            )
        builder.row(
            InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin_add_admin")
        )
        builder.row(
            InlineKeyboardButton(text="🔙 В меню", callback_data="admin_back_to_main")
        )
        return builder.as_markup()
    except (KeyError, TypeError) as e:
        logger.error(f"Data error in admins_list_kb: {e}")
        return InlineKeyboardMarkup()
    except Exception as e:
        logger.error(f"Unexpected error in admins_list_kb: {e}")
        return InlineKeyboardMarkup()

def admin_add_kb() -> InlineKeyboardMarkup:
    try:
        builder = InlineKeyboardBuilder()
        builder.row(
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_cancel_add_admin")
        )
        return builder.as_markup()
    except Exception as e:
        logger.error(f"Unexpected error in admin_add_kb: {e}")
        return InlineKeyboardMarkup()
