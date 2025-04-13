import logging

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from fluentogram import TranslatorRunner
from typing import Union

from services import user_req, vpn_req
from keyboards import main_kb, devices_kb

devices_router = Router()

logger = logging.getLogger(__name__)

# IS CORRECT FOR ALL DEVICES??
DEVICE_PRICE = "?????" 

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')


@devices_router.message(F.text.in_(['', ''])) # FILL CORRECT MESSAGES!
@devices_router.callback_query(F.data == 'devices_menu')
async def devices_button_handler(event: Union[CallbackQuery, Message],
                                 i18n: TranslatorRunner):
    
    user_id = event.from_user.id

    # ??? Add to Backend users model IN GET_USER !!!
    user = await user_req.get_user(user_id)
    devices = user.devices
    combo_cells = user.combo_cells
    subscription_fee = devices * DEVICE_PRICE # NEED TO KNOW

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text=i18n.devices.menu(subscription_fee=subscription_fee),
                                       reply_markup=devices_kb.devices_kb(i18n, devices, combo_cells))
    elif isinstance(event, Message):
        await event.answer(text=i18n.devices.menu(subscription_fee=subscription_fee),
                           reply_markup=devices_kb.devices_kb(i18n, devices, combo_cells))
        

@devices_router.callback_query(F.data.startswith("selected_device_"))
async def select_device_handler(callback: CallbackQuery,
                                i18n: TranslatorRunner):
    
    user_id = callback.from_user.id
    _, _, device = callback.data.split('_')
    device_key = await vpn_req.get_device_key(user_id, device)

    await callback.message.edit_text(text=i18n.device.menu(device=device, device_key=device_key),
                                     reply_markup=devices_kb.device_kb(i18n, device))
    

@devices_router.callback_query(F.data == 'add_device')
async def add_device_handler(callback: CallbackQuery,
                             i18n: TranslatorRunner):
    
    await callback.message.edit_text(text=i18n.add.device.menu,
                                     reply_markup = devices_kb.add_devices_kb(i18n))
    

@devices_router.message((F.text.in_({'', ''})) | (F.text.in_({'', ''})))  # DEVICE OR COMBO ON RU/EN
async def select_device_type(message: Message,
                             state: FSMContext,
                             i18n: TranslatorRunner):
    
    device_type = message.text
    # ADDITIONAL LOGIC TO CLASSIFICATE DEVICE_TYPE
    await state.update_data(device_type=device_type)
    await message.answer(text=i18n.devices.category.menu, reply_markup=devices_kb(i18n, device_type))


@devices_router.message(F.text.in_({'android', 'iphone', 'windows', 'macos', 'tv', 'router'}))
async def select_device_handler(message: Message,
                                state: FSMContext,
                                i18n: TranslatorRunner):
    
    device = message.text
    user_id = message.from_user.id
    user = await user_req.get_user(user_id)
    balance = user.balance
    is_subscripted = user.is_subscripted

    await state.update_data(device=device, balance=balance, is_subscripted=is_subscripted)
    await message.answer(text=i18n.period.menu(balance=balance, is_subscripted=is_subscripted), 
                         reply_markup=devices_kb.period_select_kb(i18n))
    

@devices_router.callback_query(F.data.startswith('month_'))
async def select_period_handler(callback: CallbackQuery,
                                state: FSMContext,
                                i18n: TranslatorRunner):
    
    _, period = callback.data.split('_') 
    payment_type = 'buy_subscription'
    await state.update_data(period=period, payment_type=payment_type)
    state_data = await state.get_data()
    balance = state_data['balance']
    is_subscripted = state_data['is_subscripted']

    await callback.message.edit_text(text=i18n.payment.menu(balance=balance, is_subscripted=is_subscripted),
                                     reply_markup=devices_kb.payment_select(i18n, payment_type))

    

