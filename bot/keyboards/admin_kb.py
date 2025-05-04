import logging
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from fluentogram import TranslatorRunner

logger = logging.getLogger(__name__)

def admin_main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 Пользователи"),
                KeyboardButton(text="🔑 Ключи")
            ],
            [
                KeyboardButton(text="💰 Финансы"),
                KeyboardButton(text="📢 Рассылка")
            ],
            [
                KeyboardButton(text="🛡 Безопасность")
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )

def users_list_kb(users, page, per_page):
    keyboard = []
    row = []
    for idx, user in enumerate(users):
        btn = InlineKeyboardButton(
            text=f"{user['user_id']}",
            callback_data=f"admin_user_{user['user_id']}"
        )
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="🔍 Поиск", callback_data="admin_user_search")])

    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_users_page_{page-1}"))
    nav_row.append(InlineKeyboardButton(text=f"Стр. {page+1}", callback_data="noop"))
    if len(users) == per_page:
        nav_row.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"admin_users_page_{page+1}"))
    keyboard.append(nav_row)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
