import logging

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery, ContentType
from fluentogram import TranslatorRunner
from typing import Union

from services import admin_req
from services.states import AdminSG
from keyboards import admin_kb

admin_router = Router()
admin = get_config(Admin, 'admin')  # BUILD IT
admin_id = admin.id

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


@admin_router.callback_query(F.data.startswith("reply_ticket_"))
async def reply_ticket_start(callback: CallbackQuery, 
                             i18n: TranslatorRunner,
                             state: FSMContext):

    if str(callback.from_user.id) != str(admin_id):
        await callback.answer(i18n.error.only.admin(), show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[2])
    
    await state.update_data(user_id=user_id)
    await state.set_state(AdminSG.reply_ticket)
    await callback.message.answer(i18n.reply.ticket())
    await callback.answer()


@account_router.message(AdminSG.reply_ticket)
async def process_ticket_reply(message: Message, 
                               bot: Bot, 
                               state: FSMContext, 
                               i18n: TranslatorRunner):
    
    if str(message.from_user.id) != str(admin_id):
        await message.answer(i18n.error.only.admin())
        return
    
    reply_text = message.text
    data = await state.get_data()
    user_id = data.get("user_id")
    
    await bot.send_message(
        user_id,
        text=i18n.ticket.answer(reply_text=reply_text)
    )

    await db.delete_ticket(user_id)
    await message.answer(i18n.admin.answer())
        