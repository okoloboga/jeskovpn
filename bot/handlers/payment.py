import logging

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery, ContentType
from aiogram.types import 
from fluentogram import TranslatorRunner

from services import user_req, payment_req
from keyboards import main_kb, devices_kb

payment_router = Router()

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')

month_price = {'normal':    {'1': '149',
                             '3': '400',
                             '6': '625',
                             '12': '900'},
               'pro':       {'1': '350',
                             '3': '945',
                             '6': '1470',
                             '12': '2100'},
               'combo_5':   {'1': '750',
                             '3': '2000',
                             '6': '3150',
                             '12': '4500'},
               'combo_10':  {'1': '1500',
                             '3': '4000',
                             '6': '6300',
                             '12': '9000'}
                }


@payment_router.callback_query(F.data.startswith('payment_'))
async def payment_handler(callback: CallbackQuery,
                          state: FSMContext,
                          bot: Bot,
                          i18n: TranslatorRunner):
    
    _, method = callback.data.split('_')
    user_id = callback.from_user.id
    state_data = await state.get_data()
    period = state_data['period']
    device_type = state_data['device_type']
    amount = month_price[device_type][period]

    if method == 'ukassa':
        await payment_req.payment_ukassa_process(user_id, amount)
    elif method == 'crypto':
        await payment_req.payment_crypto_process(user_id, amount)
    elif method == 'balance':
        await payment_req.payment_balance_process(user_id, amount)
    elif method == 'stars':
        await bot.send_invoice(
            chat_id=callback.chat.id,
            title=i18n.stars.subscription.title,
            description=i18n.stars.subscription.description,
            payload="vpn_subscription",
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(label=i18n.payment.label, amount=100)],
            start_parameter="vpn-subscription"
        )

# NEED TO GET OFFICIAL METHODS:

@payment_router.pre_checkout_query_handler(lambda query: True)
async def pre_checkout(pre_checkout_query: PreCheckoutQuery,
                       bot: Bot):
    
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@payment_router.message(content_types=ContentType.SUCCESSFUL_PAYMENT)
async def process_payment(message: Message,
                          i18n: TranslatorRunner):

    payment = message.successful_payment
    await message.answer(text=i18n.stars.payment.successfull(payload=payment.invoice_payload))