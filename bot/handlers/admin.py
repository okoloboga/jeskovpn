import logging
from typing import Optional
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from fluentogram import TranslatorRunner

from services import admin_req, AdminAuthStates
from utils.admin_auth import is_admin
from keyboards import admin_kb
from config import get_config, Admin

admin_router = Router()
admin = get_config(Admin, "admin")
admin_id = admin.id 
PER_PAGE = 20

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s:%(lineno)d #%(levelname)-8s "
           "[%(asctime)s] - %(name)s - %(message)s"
)

@admin_router.message(F.text == "/admin")
async def admin_entry(
        message: Message, 
        state: FSMContext,
        i18n: TranslatorRunner
) -> None:

    user_id = message.from_user.id
    if not is_admin(str(user_id), admin_id):
        logger.info(f'not admin. user_id: {user_id}, admin_id: {admin_id}')
        await message.answer(text=i18n.unknown.message())
        return

    if not await admin_req.has_admin_password(user_id):
        await message.answer("Добро пожаловать! Установите новый пароль для входа в админ-панель:")
        await state.set_state(AdminAuthStates.waiting_for_new_password)
    else:
        await message.answer("Введите пароль для входа в админ-панель:")
        await state.set_state(AdminAuthStates.waiting_for_password)

@admin_router.message(AdminAuthStates.waiting_for_new_password)
async def admin_set_password(
        message: Message, 
        state: FSMContext
) -> None:

    user_id = message.from_user.id
    password = message.text.strip()

    if len(password) < 6:
        await message.answer("Пароль слишком короткий. Минимум 6 символов.")
        return

    ok = await admin_req.set_admin_password(user_id, password)
    
    if ok:
        await message.answer("Пароль установлен! Вы вошли в админ-панель.",
                             reply_markup=admin_kb.admin_main_menu_kb())
        await state.clear()
    
    else:
        await message.answer("Ошибка при установке пароля. Попробуйте ещё раз.")

@admin_router.message(AdminAuthStates.waiting_for_password)
async def admin_check_password(
        message: Message, 
        state: FSMContext
) -> None:
    
    user_id = message.from_user.id
    password = message.text.strip()
    ok = await admin_req.check_admin_password(user_id, password)
    
    if ok:
        await message.answer("Вход выполнен! Добро пожаловать в админ-панель.",
                             reply_markup=admin_kb.admin_main_menu_kb())
        await state.clear()
    else:
        await message.answer("Неверный пароль. Попробуйте ещё раз.")

@admin_router.message(F.text == "👤 Пользователи")
async def admin_users_menu(
        message: Message, 
        state: FSMContext
) -> None:

    summary = await admin_req.get_users_summary()
    if not summary:
        return await message.answer("Ошибка получения данных.")
    total = summary["total"]
    active = summary["active"]
    text = (
        f"👥 Всего пользователей: <b>{total}</b>\n"
        f"🟢 С активной подпиской: <b>{active}</b>"
    )
    users = await admin_req.get_users(skip=0, limit=PER_PAGE)
    await message.answer(
        text,
        reply_markup=admin_kb.users_list_kb(users, page=0, per_page=PER_PAGE),
        parse_mode="HTML"
    )

@admin_router.callback_query(F.data.startswith("admin_users_page_"))
async def admin_users_pagination(
        callback: CallbackQuery
) -> None:
    
    page = int(callback.data.split("_")[-1])
    skip = page * PER_PAGE
    users = await admin_req.get_users(skip=skip, limit=PER_PAGE)
    await callback.message.edit_reply_markup(
        reply_markup=admin_kb.users_list_kb(users, page=page, per_page=PER_PAGE)
    )
    await callback.answer()
