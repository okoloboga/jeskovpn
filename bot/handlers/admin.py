import logging
import re
import json

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from fluentogram import TranslatorRunner

from services import admin_req, payment_req, AdminAuthStates
from utils.admin_auth import is_admin
from keyboards import admin_kb
from config import get_config, Admin

admin_router = Router()
admin = get_config(Admin, "admin")
admin_id = admin.id 
PER_PAGE = 20

logger = logging.getLogger(__name__)
admin_logger = logging.getLogger("admin_actions")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s:%(lineno)d #%(levelname)-8s "
           "[%(asctime)s] - %(name)s - %(message)s"
)
admin_handler = logging.FileHandler("admin_actions.log")
admin_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
))
admin_logger.addHandler(admin_handler)
admin_logger.setLevel(logging.INFO)

@admin_router.message(F.text == "/admin")
async def admin_entry(
        message: Message, 
        state: FSMContext,
        i18n: TranslatorRunner
) -> None:
    user_id = message.from_user.id

    logger.info(f'ID: {user_id}; ADMINS: {admin_id}')
    is_admin_check = await is_admin(str(user_id), admin_id)
    if not is_admin_check:
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
        admin_logger.info(f"Admin {user_id} set password")
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
        admin_logger.info(f"Admin {user_id} logged in")
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
        reply_markup=admin_kb.users_list_kb(users, page=0, per_page=PER_PAGE)
    )
    admin_logger.info(f"Admin {message.from_user.id} viewed users list")

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
    admin_logger.info(f"Admin {callback.from_user.id} viewed users page {page+1}")
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_user_profile_"))
async def admin_user_profile(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[-1])
    users = await admin_req.get_users(user_id=user_id)
    if not users:
        await callback.message.answer("Пользователь не найден.")
        return
    user = users[0]  # Берем первого пользователя из списка
    subscription = user["subscription"]
    text = (
        f"👤 Пользователь: {user['username'] or user['first_name'] or 'N/A'} (ID: {user_id})\n"
        f"\n📧 Email: {user.get('email_address', 'N/A')}\n"
        f"📱 Номер телефона: {user.get('phone_number', 'N/A')}\n"
        f"\n💰 Баланс: {user.get('balance', 0.0)}\n"
        f"\n📅 Регистрация: {user.get('created_at', 'N/A')}\n"
        f"\n📱 Подписки:\n"
    )
    if subscription["device"]["duration"] > 0:
        text += f"  - Устройство: {subscription['device']['duration']} дней, "
        text += f"устройства: {', '.join(subscription['device']['devices']) or 'нет'}\n"
    if subscription["router"]["duration"] > 0:
        text += f"  - Роутер: {subscription['router']['duration']} дней, "
        text += f"устройства: {', '.join(subscription['router']['devices']) or 'нет'}\n"
    if subscription["combo"]["duration"] > 0:
        text += f"  - Комбо ({subscription['combo']['type']}): {subscription['combo']['duration']} дней, "
        text += f"устройства: {', '.join(subscription['combo']['devices']) or 'нет'}\n"
    await callback.message.answer(
        text,
        reply_markup=admin_kb.user_profile_kb(user_id, is_blacklisted=user.get("is_blacklisted", False))

    )
    admin_logger.info(f"Admin {callback.from_user.id} viewed profile of user {user_id}")
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_add_balance_"))
async def admin_add_balance_start(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[-1])
    await state.update_data(user_id=user_id)
    await callback.message.answer("Введите сумму для пополнения баланса (например, 1000.50):")
    await state.set_state(AdminAuthStates.add_balance)
    await callback.answer()

@admin_router.message(AdminAuthStates.add_balance)
async def admin_add_balance_amount(message: Message, state: FSMContext):
    amount_text = message.text.strip()
    try:
        amount = float(amount_text)
        if amount <= 0:
            await message.answer("Сумма должна быть больше 0. Попробуйте снова:")
            return
    except ValueError:
        await message.answer("Сумма должна быть числом (например, 1000.50). Попробуйте снова:")
        return
    
    data = await state.get_data()
    user_id = data["user_id"]
    await state.update_data(amount=amount)
    
    # Клавиатура подтверждения
    confirm_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"admin_confirm_balance_{user_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="admin_cancel_balance")
        ]
    ])
    await message.answer(
        f"Пополнить баланс ID {user_id} на {amount}?",
        reply_markup=confirm_kb
    )

@admin_router.callback_query(F.data.startswith("admin_confirm_balance_"))
async def admin_confirm_balance(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    amount = data.get("amount")
    
    if not amount:
        await callback.message.answer("Ошибка: сумма не найдена.")
        await state.clear()
        await callback.answer()
        return
    
    # Вызов payment_balance_process
    result = await payment_req.payment_balance_process(
        user_id=user_id,
        amount=amount,
        period=0,
        device_type="balance",
        device="balance",
        payment_type="add_balance",
        method="admin"
    )
    
    if result:
        await callback.message.answer(f"Баланс пользователя {user_id} пополнен на {amount}.")
        admin_logger.info(f"Admin {callback.from_user.id} added balance {amount} to user {user_id}")
        
        # Обновляем профиль пользователя
        users = await admin_req.get_users(user_id=user_id)
        if users:
            user = users[0]
            subscription = user["subscription"]
            text = (
                f"👤 Пользователь: {user['username'] or user['first_name'] or 'N/A'} (ID: {user_id})\n"
                f"\n📧 Email: {user.get('email_address', 'N/A')}\n"
                f"\n💰 Баланс: {user.get('balance', 0.0)}\n"
                f"\n📅 Регистрация: {user.get('created_at', 'N/A')}\n"
                f"\n📱 Подписки:\n"
            )
            if subscription["device"]["duration"] > 0:
                text += f"  - Устройство: {subscription['device']['duration']} дней, "
                text += f"устройства: {', '.join(subscription['device']['devices']) or 'нет'}\n"
            if subscription["router"]["duration"] > 0:
                text += f"  - Роутер: {subscription['router']['duration']} дней, "
                text += f"устройства: {', '.join(subscription['router']['devices']) or 'нет'}\n"
            if subscription["combo"]["duration"] > 0:
                text += f"  - Комбо ({subscription['combo']['type']}): {subscription['combo']['duration']} дней, "
                text += f"устройства: {', '.join(subscription['combo']['devices']) or 'нет'}\n"
            await callback.message.edit_text(
                text,
                reply_markup=admin_kb.user_profile_kb(user_id, is_blacklisted=user.get("is_blacklisted", False)),
                parse_mode="HTML"
            )
    else:
        await callback.message.answer(f"Ошибка пополнения баланса пользователя {user_id}.")
        admin_logger.error(f"Admin {callback.from_user.id} failed to add balance {amount} to user {user_id}")
    
    await state.clear()
    await callback.answer()

@admin_router.callback_query(F.data == "admin_cancel_balance")
async def admin_cancel_balance(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Пополнение баланса отменено.")
    await state.clear()
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_unblock_user_"))
async def admin_unblock_user(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[-1])
    
    success = await admin_req.remove_from_blacklist(user_id)
    if success:
        await callback.message.answer(f"Пользователь {user_id} разблокирован.")
        admin_logger.info(f"Admin {callback.from_user.id} unblocked user {user_id}")
    else:
        await callback.message.answer(f"Ошибка разблокировки пользователя {user_id}.")
        admin_logger.error(f"Admin {callback.from_user.id} failed to unblock user {user_id}")
    
    # Обновляем профиль пользователя
    users = await admin_req.get_users(user_id=user_id)
    if users:
        user = users[0]
        subscription = user["subscription"]
        text = (
            f"👤 Пользователь: {user['username'] or user['first_name'] or 'N/A'} (ID: {user_id})\n"
            f"\n📧 Email: {user.get('email_address', 'N/A')}\n"
            f"\n💰 Баланс: {user.get('balance', 0.0)}\n"
            f"\n📅 Регистрация: {user.get('created_at', 'N/A')}\n"
            f"\n📱 Подписки:\n"
        )
        if subscription["device"]["duration"] > 0:
            text += f"  - Устройство: {subscription['device']['duration']} дней, "
            text += f"устройства: {', '.join(subscription['device']['devices']) or 'нет'}\n"
        if subscription["router"]["duration"] > 0:
            text += f"  - Роутер: {subscription['router']['duration']} дней, "
            text += f"устройства: {', '.join(subscription['router']['devices']) or 'нет'}\n"
        if subscription["combo"]["duration"] > 0:
            text += f"  - Комбо ({subscription['combo']['type']}): {subscription['combo']['duration']} дней, "
            text += f"устройства: {', '.join(subscription['combo']['devices']) or 'нет'}\n"
        await callback.message.edit_text(
            text,
            reply_markup=admin_kb.user_profile_kb(user_id, is_blacklisted=user.get("is_blacklisted", False))

        )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_block_user_"))
async def admin_block_user(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[-1])
    
    success = await admin_req.block_user(user_id)
    if success:
        await callback.message.answer(f"Пользователь {user_id} заблокирован.")
        admin_logger.info(f"Admin {callback.from_user.id} blocked user {user_id}")
    else:
        await callback.message.answer(f"Ошибка блокировки пользователя {user_id}.")
        admin_logger.error(f"Admin {callback.from_user.id} failed to block user {user_id}")
    
    # Обновляем профиль пользователя
    users = await admin_req.get_users(user_id=user_id)
    if users:
        user = users[0]
        subscription = user["subscription"]
        text = (
            f"👤 Пользователь: {user['username'] or user['first_name'] or 'N/A'} (ID: {user_id})\n"
            f"\n📧 Email: {user.get('email_address', 'N/A')}\n"
            f"\n💰 Баланс: {user.get('balance', 0.0)}\n"
            f"\n📅 Регистрация: {user.get('created_at', 'N/A')}\n"
            f"\n📱 Подписки:\n"
        )
        if subscription["device"]["duration"] > 0:
            text += f"  - Устройство: {subscription['device']['duration']} дней, "
            text += f"устройства: {', '.join(subscription['device']['devices']) or 'нет'}\n"
        if subscription["router"]["duration"] > 0:
            text += f"  - Роутер: {subscription['router']['duration']} дней, "
            text += f"устройства: {', '.join(subscription['router']['devices']) or 'нет'}\n"
        if subscription["combo"]["duration"] > 0:
            text += f"  - Комбо ({subscription['combo']['type']}): {subscription['combo']['duration']} дней, "
            text += f"устройства: {', '.join(subscription['combo']['devices']) or 'нет'}\n"
        await callback.message.edit_text(
            text,
            reply_markup=admin_kb.user_profile_kb(user_id, is_blacklisted=user.get("is_blacklisted", False))

        )
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_delete_user_"))
async def admin_delete_user(callback: CallbackQuery):
    user_id = int(callback.data.split("_")[-1])
    if str(user_id) == admin_id:
        await callback.message.answer("Нельзя удалить администратора.")
        return
    success = await admin_req.delete_user(user_id)
    await callback.message.answer(
        "Пользователь удален." if success else "Ошибка удаления."
    )
    admin_logger.info(f"Admin {callback.from_user.id} deleted user {user_id}")
    await callback.answer()

@admin_router.callback_query(F.data == "admin_back_to_users")
async def admin_back_to_users(callback: CallbackQuery):
    summary = await admin_req.get_users_summary()
    if not summary:
        await callback.message.answer("Ошибка получения данных.")
        return
    total = summary["total"]
    active = summary["active"]
    text = (
        f"👥 Всего пользователей: <b>{total}</b>\n"
        f"🟢 С активной подпиской: <b>{active}</b>"
    )
    users = await admin_req.get_users(skip=0, limit=PER_PAGE)
    await callback.message.answer(
        text,
        reply_markup=admin_kb.users_list_kb(users, page=0, per_page=PER_PAGE)
    )
    admin_logger.info(f"Admin {callback.from_user.id} returned to users list")
    await callback.answer()

@admin_router.callback_query(F.data == "admin_back_to_main")
async def admin_back_to_main(callback: CallbackQuery):
    await callback.message.answer(
        "Админ-панель",
        reply_markup=admin_kb.admin_main_menu_kb()
    )
    admin_logger.info(f"Admin {callback.from_user.id} returned to main menu")
    await callback.answer()

@admin_router.message(F.text == "🔑 Ключи")
async def admin_keys_menu(message: Message, state: FSMContext):
    keys = await admin_req.get_keys(skip=0, limit=PER_PAGE)
    if not keys:
        await message.answer("Ключи не найдены.")
        return
    await message.answer(
        "🔑 Список ключей:",
        reply_markup=admin_kb.keys_list_kb(keys, page=0, per_page=PER_PAGE)
    )
    admin_logger.info(f"Admin {message.from_user.id} viewed keys list")

@admin_router.callback_query(F.data.startswith("admin_keys_page_"))
async def admin_keys_pagination(callback: CallbackQuery):
    page = int(callback.data.split("_")[-1])
    skip = page * PER_PAGE
    keys = await admin_req.get_keys(skip=skip, limit=PER_PAGE)
    await callback.message.edit_reply_markup(
        reply_markup=admin_kb.keys_list_kb(keys, page=page, per_page=PER_PAGE)
    )
    admin_logger.info(f"Admin {callback.from_user.id} viewed keys page {page+1}")
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_key_profile_"))
async def admin_key_profile(callback: CallbackQuery):
    vpn_key = callback.data.split("_")[-1]
    keys = await admin_req.get_keys(vpn_key=vpn_key)
    if not keys:
        await callback.message.answer("Ключ не найден.")
        return
    key = keys[0]
    status = "Активен" if key['is_active'] else "Неактивен"
    text = (
        f"🔑 Ключ: {key['vpn_key']}\n"
        f"\n🆔 Outline ID: {key['outline_key_id'] or 'N/A'}\n"
        f"👤 Пользователь: {key['user_id']}\n"
        f"📱 Тип: {key['device_type']}\n"
        f"\n📅 Начало: {key['start_date']}\n"
        f"📅 Окончание: {key['end_date']}\n"
        f"\n🟢 Статус: {status}"
    )
    await callback.message.answer(
        text,
        reply_markup=admin_kb.key_profile_kb(vpn_key)
    )
    admin_logger.info(f"Admin {callback.from_user.id} viewed key {vpn_key}")
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_key_history_"))
async def admin_key_history(callback: CallbackQuery):
    vpn_key = callback.data.split("_")[-1]
    history = await admin_req.get_key_history(vpn_key)
    if not history:
        await callback.message.answer("История для этого ключа не найдена.")
        return
    text = f"📜 История ключа {vpn_key}:\n\n"
    for idx, entry in enumerate(history, 1):
        text += (
            f"Запись {idx}:\n"
            f"👤 Пользователь: {entry['user_id']}\n"
            f"📱 Тип: {entry['device_type']}\n"
            f"🖥 Имя: {entry['device_name'] or 'N/A'}\n"
            f"\n📅 Начало: {entry['start_date']}\n"
            f"\n📅 Окончание: {entry['end_date']}\n\n"
        )
    await callback.message.answer(text)
    admin_logger.info(f"Admin {callback.from_user.id} viewed history of key {vpn_key}")
    await callback.answer()

@admin_router.callback_query(F.data == "admin_back_to_keys")
async def admin_back_to_keys(callback: CallbackQuery):
    keys = await admin_req.get_keys(skip=0, limit=PER_PAGE)
    if not keys:
        await callback.message.answer("Ключи не найдены.")
        return
    await callback.message.answer(
        "🔑 Список ключей:",
        reply_markup=admin_kb.keys_list_kb(keys, page=0, per_page=PER_PAGE)
    )
    admin_logger.info(f"Admin {callback.from_user.id} returned to keys list")
    await callback.answer()

@admin_router.message(F.text == "💰 Финансы")
async def admin_finance_menu(message: Message, state: FSMContext):
    summary = await admin_req.get_payments_summary()
    if not summary:
        await message.answer("Ошибка получения статистики.")
        return
    
    text = "📊 Финансовая статистика (в RUB):\n\n"
    
    # За день
    text += "📅 За последний день:\n"
    text += f"💸 Сумма: {summary['day']['total_amount']} RUB\n"
    text += f"📈 Платежи: {summary['day']['total_count']}\n"
    for method, data in summary['day']['by_method'].items():
        text += f"  - {method}: {data['amount']} RUB ({data['count']} платежей)\n"
    
    # За месяц
    text += "\n📅 За последний месяц:\n"
    text += f"💸 Сумма: {summary['month']['total_amount']} RUB\n"
    text += f"📈 Платежи: {summary['month']['total_count']}\n"
    for method, data in summary['month']['by_method'].items():
        text += f"  - {method}: {data['amount']} RUB ({data['count']} платежей)\n"
    
    # За всё время
    text += "\n📅 За всё время:\n"
    text += f"💸 Сумма: {summary['all_time']['total_amount']} RUB\n"
    text += f"📈 Платежи: {summary['all_time']['total_count']}\n"
    for method, data in summary['all_time']['by_method'].items():
        text += f"  - {method}: {data['amount']} RUB ({data['count']} платежей)\n"
    
    await message.answer(
        text,
        reply_markup=admin_kb.finance_menu_kb()
    )
    admin_logger.info(f"Admin {message.from_user.id} viewed finance summary")

@admin_router.message(F.text == "📢 Рассылка")
async def admin_broadcast_menu(message: Message, state: FSMContext):
    await message.answer(
        "Введите текст для рассылки:",
        reply_markup=admin_kb.broadcast_menu_kb()
    )
    await state.set_state(AdminAuthStates.waiting_for_broadcast_message)
    admin_logger.info(f"Admin {message.from_user.id} started broadcast")

@admin_router.message(AdminAuthStates.waiting_for_broadcast_message)
async def admin_broadcast_receive_message(message: Message, state: FSMContext, bot: Bot):
    text = message.text.strip()
    if not text:
        await message.answer("Текст не может быть пустым. Введите текст:")
        return
    if len(text) > 4096:
        await message.answer("Текст слишком длинный (максимум 4096 символов). Введите короче:")
        return
    
    user_ids = await admin_req.get_all_users()
    if not user_ids:
        await message.answer("Пользователи не найдены.")
        await state.clear()
        return
    
    success_count = 0
    fail_count = 0
    for user_id in user_ids:
        try:
            await bot.send_message(chat_id=user_id, text=text)
            success_count += 1
        except Exception as e:
            admin_logger.error(f"Broadcast to user {user_id} failed: {e}")
            fail_count += 1
    
    await message.answer(
        f"Рассылка завершена:\n✅ Успешно: {success_count}\n❌ Неуспешно: {fail_count}"
    )
    admin_logger.info(f"Admin {message.from_user.id} sent broadcast: {success_count} success, {fail_count} failed")
    await state.clear()

@admin_router.callback_query(F.data == "admin_broadcast_send")
async def admin_broadcast_send(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Рассылка уже выполняется или текст не введен. Начните заново.")
    await state.clear()
    await callback.answer()

@admin_router.callback_query(F.data == "admin_broadcast_cancel")
async def admin_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Рассылка отменена.")
    admin_logger.info(f"Admin {callback.from_user.id} canceled broadcast")
    await state.clear()
    await callback.answer()

@admin_router.message(F.text == "🛡 Безопасность")
async def admin_security_menu(message: Message):
    admins = await admin_req.get_admins()
    if not admins:
        await message.answer(
            "Админы не найдены.",
            reply_markup=admin_kb.admins_list_kb(admins)
        )
    else:
        await message.answer(
            ("🛡 Список админов.\n" +
            "Для удаления из админов - нажмите на него:"),
            reply_markup=admin_kb.admins_list_kb(admins)
        )
    admin_logger.info(f"Admin {message.from_user.id} viewed admins list")

@admin_router.callback_query(F.data == "admin_add_admin")
async def admin_add_admin_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "Введите user_id нового админа:",
        reply_markup=admin_kb.admin_add_kb()
    )
    await state.set_state(AdminAuthStates.waiting_for_new_admin_id)
    admin_logger.info(f"Admin {callback.from_user.id} started adding new admin")
    await callback.answer()

@admin_router.message(AdminAuthStates.waiting_for_new_admin_id)
async def admin_add_admin_receive_id(message: Message, state: FSMContext):
    user_id_text = message.text.strip()
    if not user_id_text.isdigit():
        await message.answer("user_id должен быть числом. Попробуйте снова:")
        return
    user_id = int(user_id_text)
    
    success = await admin_req.add_admin(user_id)
    if success:
        await message.answer(f"Админ {user_id} добавлен.")
        admin_logger.info(f"Admin {message.from_user.id} added admin {user_id}")
    else:
        await message.answer("Ошибка добавления админа. Возможно, он уже админ или сервер недоступен.")
        admin_logger.error(f"Admin {message.from_user.id} failed to add admin {user_id}")
    
    admins = await admin_req.get_admins()
    await message.answer(
        "🛡 Список админов:",
        reply_markup=admin_kb.admins_list_kb(admins)
    )
    await state.clear()

@admin_router.callback_query(F.data.startswith("admin_remove_admin_"))
async def admin_remove_admin(callback: CallbackQuery):
    admin_id = int(callback.data.split("_")[-1])
    if admin_id == callback.from_user.id:
        await callback.message.answer("Нельзя удалить самого себя.")
        await callback.answer()
        return
    
    success = await admin_req.delete_admin(admin_id)

    if success:
        await callback.message.answer(f"Админ {admin_id} удален.")
        admin_logger.info(f"Admin {callback.from_user.id} removed admin {admin_id}")
    else:
        await callback.message.answer("Ошибка удаления админа.")
        admin_logger.error(f"Admin {callback.from_user.id} failed to remove admin {admin_id}: {success}")
    
    admins = await admin_req.get_admins()
    await callback.message.answer(
        "🛡 Список админов:",
        reply_markup=admin_kb.admins_list_kb(admins)
    )
    await callback.answer()

@admin_router.callback_query(F.data == "admin_cancel_add_admin")
async def admin_cancel_add_admin(callback: CallbackQuery, state: FSMContext):
    admins = await admin_req.get_admins()
    await callback.message.answer(
        "Добавление админа отменено.",
        reply_markup=admin_kb.admins_list_kb(admins)
    )
    admin_logger.info(f"Admin {callback.from_user.id} canceled adding admin")
    await state.clear()
    await callback.answer()

@admin_router.message(F.text == "🔍 Поиск пользователей")
async def admin_search_users_start(message: Message, state: FSMContext):
    await message.answer("Введите запрос для поиска (username, ID, email, имя, телефон):")
    await state.set_state(AdminAuthStates.search_users)

@admin_router.message(AdminAuthStates.search_users)
async def admin_search_users_process(message: Message, state: FSMContext):
    query = message.text.strip()
    if not query:
        await message.answer("Запрос не может быть пустым. Попробуйте снова:")
        return
    
    users = await admin_req.get_users(query=query, skip=0, limit=20)
    if not users:
        await message.answer("Пользователи не найдены.")
        await state.clear()
        return
    
    admin_logger.info(f"Admin {message.from_user.id} searched users with query '{query}'")
    await message.answer(
        "📋 Результаты поиска:",
        reply_markup=admin_kb.users_list_kb(users, page=0, per_page=20),
        parse_mode="HTML"
    )
    await state.clear()


@admin_router.message(F.text == "🎟 Промокоды")
async def admin_promocodes_start(message: Message):
    promocodes = await admin_req.get_promocodes(skip=0, limit=20)
    if not promocodes:
        await message.answer(
            "Промокоды не найдены.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="➕ Добавить код", callback_data="admin_add_promocode"),
                InlineKeyboardButton(text="🔙 В меню", callback_data="admin_back_to_main")
            ]])
        )
        return
    
    admin_logger.info(f"Admin {message.from_user.id} viewed promocodes list")
    await message.answer(
        "📋 Список промокодов:",
        reply_markup=admin_kb.promocodes_list_kb(promocodes, page=0, per_page=20),
        parse_mode="HTML"
    )

@admin_router.callback_query(F.data.startswith("admin_promocodes_page_"))
async def admin_promocodes_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[-1])
    promocodes = await admin_req.get_promocodes(skip=page * 20, limit=20)
    if not promocodes:
        await callback.message.edit_text(
            "Промокоды не найдены.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="➕ Добавить код", callback_data="admin_add_promocode"),
                InlineKeyboardButton(text="🔙 В меню", callback_data="admin_back_to_main")
            ]])
        )
        return
    
    await callback.message.edit_text(
        "📋 Список промокодов:",
        reply_markup=admin_kb.promocodes_list_kb(promocodes, page=page, per_page=20),
        parse_mode="HTML"
    )
    await callback.answer()

@admin_router.callback_query(F.data == "admin_add_promocode")
async def admin_add_promocode_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите код промокода (только буквы и цифры):")
    await state.set_state(AdminAuthStates.add_promo_code)
    await callback.answer()

@admin_router.message(AdminAuthStates.add_promo_code)
async def admin_add_promocode_code(message: Message, state: FSMContext):
    code = message.text.strip()
    if not re.match(r"^[a-zA-Z0-9]+$", code):
        await message.answer("Код должен содержать только буквы и цифры. Попробуйте снова:")
        return
    
    await state.update_data(code=code)
    await message.answer(
        str("Введите тип промокода\n\n") +
        "Для создания промокода на пополнения баланса введите: balance_СУММА\n\n" +
        "Промокод подписки на 1 устройство (1 месяц): device_promo\n" +
        "Промокод кобмо: combo_5 или combo_10")
    await state.set_state(AdminAuthStates.add_promo_type)

@admin_router.message(AdminAuthStates.add_promo_type)
async def admin_add_promocode_type(message: Message, state: FSMContext):
    type_ = message.text.strip().lower()
    valid_types = [
        "device_promo", "combo_5", "combo_10",
        *[f"balance_{amount}" for amount in range(1, 10001)]
    ]
    if type_ not in valid_types:
        await message.answer("Недопустимый тип промокода. Попробуйте снова:")
        return
    
    await state.update_data(type=type_)
    await message.answer("Введите максимальное количество использований (0 = без ограничений):")
    await state.set_state(AdminAuthStates.add_promo_max_usage)

@admin_router.message(AdminAuthStates.add_promo_max_usage)
async def admin_add_promocode_max_usage(message: Message, state: FSMContext):
    try:
        max_usage = int(message.text.strip())
        if max_usage < 0:
            await message.answer("Максимальное количество использований должно быть >= 0. Попробуйте снова:")
            return
    except ValueError:
        await message.answer("Введите число >= 0. Попробуйте снова:")
        return
    
    data = await state.get_data()
    code = data["code"]
    type_ = data["type"]
    
    result = await admin_req.create_promocode(code, type_, max_usage)
    if result["success"]:
        await message.answer(f"Промокод {code} создан.")
        admin_logger.info(f"Admin {message.from_user.id} created promocode {code} with type {type_}, max_usage {max_usage}")
        
        # Показываем обновлённый список
        promocodes = await admin_req.get_promocodes(skip=0, limit=20)
        if promocodes:
            await message.answer(
                "📋 Список промокодов:",
                reply_markup=admin_kb.promocodes_list_kb(promocodes, page=0, per_page=20),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "Промокоды не найдены.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="➕ Добавить код", callback_data="admin_add_promocode"),
                    InlineKeyboardButton(text="🔙 В меню", callback_data="admin_back_to_main")
                ]])
            )
    else:
        error_msg = result["error"]
        await message.answer(
            f"Ошибка создания промокода: {error_msg}\nПопробуйте ввести другой код:",
            parse_mode="HTML"
        )
        admin_logger.error(f"Admin {message.from_user.id} failed to create promocode {code}: {error_msg}")
        await state.set_state(AdminAuthStates.add_promo_code)
        return
    
    await state.clear()

@admin_router.callback_query(F.data.startswith("admin_promocode_profile_"))
async def admin_promocode_profile(callback: CallbackQuery):
    code = callback.data.split("_")[-1]
    promocodes = await admin_req.get_promocodes(code=code)
    if not promocodes:
        await callback.message.edit_text("Промокод не найден.", parse_mode="HTML")
        await callback.answer()
        return
    
    promocode = promocodes[0]
    is_active = "🟢 Активен" if promocode["is_active"] else "🔴 Неактивен"
    usage_text = f"{promocode['usage_count']}/∞" if promocode["max_usage"] == 0 else f"{promocode['usage_count']}/{promocode['max_usage']}"
    text = (
        f"<b>🎟 Промокод:</b> {promocode['code']}\n"
        f"<b>📋 Тип:</b> {promocode['type']}\n"
        f"<b>🔄 Статус:</b> {is_active}\n"
        f"<b>📊 Использований:</b> {usage_text}\n"
        f"<b>📅 Создан:</b> {promocode['created_at']}"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_kb.promocode_profile_kb(code, promocode),
        parse_mode="HTML"
    )
    admin_logger.info(f"Admin {callback.from_user.id} viewed promocode {code}")
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_deactivate_promocode_"))
async def admin_deactivate_promocode(callback: CallbackQuery):
    code = callback.data.split("_")[-1]
    result = await admin_req.delete_promocode(code)
    
    if result["success"]:
        usage_count = result["usage_count"]
        await callback.message.edit_text(
            f"Промокод <b>{code}</b> удалён.",
            parse_mode="HTML"
        )
        admin_logger.info(f"Admin {callback.from_user.id} deleted promocode {code}")
        admin_logger.info(f"Deleted {usage_count} promocode_usages for promocode {code}")
    else:
        await callback.message.edit_text(
            f"Ошибка удаления промокода: {result['error']}",
            parse_mode="HTML"
        )
        admin_logger.error(f"Admin {callback.from_user.id} failed to delete promocode {code}: {result['error']}")
    
    await callback.answer()

@admin_router.message(F.text == "🖥 Серверы Outline")
async def admin_outline_servers(
        message: Message
) -> None:
   
    servers = await admin_req.get_outline_servers()
    if not servers:
        await message.answer(
            "Нет серверов Outline.",
            reply_markup=admin_kb.outline_servers_kb(servers=[])
        )
    else:
        await message.answer(
            "<b>Серверы Outline</b>",
            parse_mode="HTML",
            reply_markup=admin_kb.outline_servers_kb(servers)
        )
    
    admin_logger.info(f"Admin {message.from_user.id} viewed outline servers")

@admin_router.callback_query(F.data == "admin_add_outline_server")
async def admin_add_outline_server(
        callback: CallbackQuery, 
        state: FSMContext
) -> None:
   
    await callback.message.edit_text(
        "Введите данные сервера в формате JSON:\n"
        'Пример: {"apiUrl":"https://example.com:12345/abc","certSha256":"847B4427DCBCBA150CF28D932AE4CA017E5024FAE3B9F54095C17051320C03E4"}',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_outline_servers")
        ]])
    )
    await state.set_state(AdminAuthStates.enter_json)
    await callback.answer()

@admin_router.message(AdminAuthStates.enter_json)
async def process_outline_server_json(
        message: Message, 
        state: FSMContext
) -> None:
    try:
        data = json.loads(message.text)
        api_url = data.get("apiUrl")
        cert_sha256 = data.get("certSha256")
        
        if not api_url or not cert_sha256:
            await message.answer("Ошибка: JSON должен содержать apiUrl и certSha256.")
            return
        
        if not re.match(r"^https?://", api_url):
            await message.answer("Ошибка: apiUrl должен начинаться с http:// или https://.")
            return
        
        if not re.match(r"^[A-F0-9]{64}$", cert_sha256):
            await message.answer("Ошибка: certSha256 должен быть 64-символьной строкой из A-F0-9.")
            return

        await state.update_data(api_url=api_url, cert_sha256=cert_sha256)
        await message.answer(
            "Введите лимит ключей для сервера (целое число больше 0):",
        )
        admin_logger.info(f"Admin {message.from_user.id} added outline server {api_url}")
        await state.set_state(AdminAuthStates.enter_key_limit)

    except json.JSONDecodeError:
        await message.answer("Ошибка: Неверный формат JSON.")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
    
    await state.clear()

@admin_router.message(AdminAuthStates.enter_key_limit)
async def process_key_limit(
        message: Message, 
        state: FSMContext
) -> None:
    try:
        key_limit = int(message.text)
        if key_limit <= 0:
            await message.answer("Ошибка: Лимит ключей должен быть больше 0.")
            return
        
        state_data = await state.get_data()
        api_url = state_data.get("api_url")
        cert_sha256 = state_data.get("cert_sha256")
        
        result = await admin_req.create_outline_server(api_url, cert_sha256, key_limit)
        if result["success"]:
            await message.answer(
                f"Сервер {api_url} добавлен с лимитом {key_limit} ключей.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="🔙 Назад", callback_data="admin_outline_servers")
                ]])
            )
            admin_logger.info(f"Admin {message.from_user.id} added outline server {api_url} with key_limit {key_limit}")
        else:
            await message.answer(f"Ошибка: {result['error']}")
    except ValueError:
        await message.answer("Ошибка: Введите целое число.")
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")
    
    await state.clear()

@admin_router.callback_query(F.data.startswith("admin_delete_outline_server_"))
async def admin_delete_outline_server(
        callback: CallbackQuery
) -> None:

    server_id = int(callback.data.split("_")[-1])
    result = await admin_req.delete_outline_server(server_id)
    if result["success"]:
        await callback.message.edit_text(
            f"Сервер {server_id} удалён."
        )
        admin_logger.info(f"Admin {callback.from_user.id} deleted outline server {server_id}")
    else:
        await callback.message.edit_text(f"Ошибка: {result['error']}")
    
    await callback.answer()

@admin_router.callback_query(F.data.startswith("admin_view_server_"))
async def admin_view_server(
        callback: CallbackQuery
) -> None:

    server_id = int(callback.data.split("_")[-1])
    servers = await admin_req.get_outline_servers()
    server = next((s for s in servers if s["id"] == server_id), None)
    
    if not server:
        await callback.message.edit_text(
            "Сервер не найден.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin_outline_servers")
            ]])
        )
        await callback.answer()
        return
    
    status = "🟢 Активен" if server["is_active"] else "🔴 Неактивен"
    text = (
        f"<b>Сервер {server['id']}</b>\n\n"
        f"ID: {server['id']}\n"
        f"URL: {server['api_url']}\n"
        f"Ключей: {server['key_count']}/{server['key_limit']}\n"
        f"Статус: {status}\n"
        f"Создан: {server['created_at']}"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=admin_kb.outline_server_menu_kb(str(server['id']))
    )
    
    admin_logger.info(f"Admin {callback.from_user.id} viewed outline server {server_id}")
    await callback.answer()
