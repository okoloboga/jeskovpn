import logging

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery, ContentType
from fluentogram import TranslatorRunner
from typing import Union

from services import user_req
from services.states import SupportSG
from keyboards import another_kb, main_kb

another_router = Router()
admin = get_config(Admin, 'admin')  # BUILD IT
admin_id = admin.id

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


@another_router.message(F.text.in_(['', ''])) # SUBSCRIPTION BUTTONS TEXT
async def subsctiption_handler(message: Message,
                               i18n: TranslatorRunner):
    
    user_id = message.from_user.id
    name = message.from_user.first_name
    if name is None or name == '':
        name = message.from_user.username

    # ??? Add to Backend users model IN GET_USER !!!
    user = await user_req.get_user(user_id)
    balance = user.balance
    is_subscripted = user.is_subscripted

    if is_subscripted:
        await message.answer(text=i18n.subscription.menu.active(name=name, balance=balance),
                             reply_markup=another_kb.subscription_menu(i18n))
    elif not is_subscripted and balance >= 149:
        await message.answer(text=i18n.nosubscription.have.balance(balance=balance),
                             reply_markup=another_kb.subscription_menu(i18n))
    else:
        await message.answer(text=i18n.nosubscription.nobalance(balance=balance),
                             reply_markup=another_kb.subscription_menu(i18n))


@another_router.message(F.text.in_(['', ''])) # SUPPORT BUTTONS TEXT
async def support_handler(message: Message,
                          i18n: TranslatorRunner):

    user_id = message.from_user.id
    ticket_data = await user_req.get_ticket_by_id(user_id)
    await state.set_state(SupportSG.create_ticket)

    ticket = ticket_data['content']
    ticket = i18n.noticket() if ticket is None else str(ticket)
    await callback.message.edit_text(i18n.ticket.menu(ticket=ticket), 
                                     reply_markup=main_kb.back_inline_kb(i18n))


@another_router.message(SupportSG.create_ticket)
async def ticket_handler(message: Message, 
                         bot: Bot, 
                         state: FSMContext, 
                         i18n: TranslatorRunner):
    
    user_id = message.from_user.id
    username = message.from_user.username
    content = message.text

    await user_req.send_ticket(content, user_id, username)
    
    await bot.send_message(
        admin_id,
        text=f'#{user_id}\n{username}:\n\n{content}',
        reply_markup=kb.reply_keyboard(user_id, i18n)
    )
    
    await message.answer(
        i18n.ticket.sended(),
        reply_markup=kb.account_menu(i18n)
    )


@another_router.message(F.text.in_(['', ''])) # REFERRALS BUTTONS TEXT