import logging
import re

from typing import Union
from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from fluentogram import TranslatorRunner

from services import services, user_req, payment_req, PaymentSG, DevicesSG, \
                     START_PRICE, MONTH_PRICE_STARS 
from keyboards import payment_kb, main_kb

payment_router = Router()

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s'
)

@payment_router.message(F.text.startswith("Баланс") | F.text.startswith("Balance") | 
                        F.text.in_(['Пополнить баланс 💰', 'Top Up Balance 💰']))
@payment_router.callback_query(F.data == "balance")
async def balance_button_handler(
    event: Union[CallbackQuery, Message],
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    """
    Handle requests to view or add balance.

    Displays the current balance and options to add funds.

    Args:
        event (Union[CallbackQuery, Message]): The incoming event (callback or message).
        state (FSMContext): Finite state machine context for storing data.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = event.from_user.id
    await state.clear()
    logger.info(f"Showing balance for user {user_id}")

    try:
        user_data = await services.get_user_data(user_id)
        user_info = await services.get_user_info(user_id)
        if user_data is None or user_info is None:
            text = i18n.error.user_not_found()
            if isinstance(event, CallbackQuery):
                await event.message.edit_text(text=text)
                await event.answer()
            else:
                await event.answer(text=text)
            return

        balance = user_data.get("balance", 0)
        month_price = user_info.get('month_price', 0)
        await state.update_data(
                balance=balance, 
                month_price=month_price
                )

        inline_keyboard = payment_kb.add_balance_kb(i18n)
        paused = user_data.get("paused", True)
        days_left = max(user_info.get("durations", (0, 0, 0))) if paused == False else 0
        is_subscribed = user_info.get('is_subscribed', False)
        text_head = i18n.balance.menu(
                        balance=balance, 
                        days=days_left
                    )
        text_tail = i18n.balance.advice()

        if isinstance(event, CallbackQuery):
            await event.message.answer(text=text_head, reply_markup=main_kb.main_kb(
                i18n=i18n,
                is_subscribed=is_subscribed,
                balance=balance,
                days_left=days_left
                ))
            await event.message.answer(text=text_tail, reply_markup=inline_keyboard)
        else:
            await event.answer(text=text_head, reply_markup=main_kb.main_kb(
                i18n=i18n,
                is_subscribed=is_subscribed,
                balance=balance,
                days_left=days_left
                ))
            await event.answer(text=text_tail, reply_markup=inline_keyboard)

    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text=i18n.error.telegram_failed())
            await event.answer()
        else:
            event.answer(text=i18n.error.telegram_failed())
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text=i18n.error.unexpected())
            await event.answer()
        else:
            await event.answer(text=i18n.error.unexpected())

@payment_router.callback_query(F.data.startswith("add_balance_"))
async def top_up_balance_handler(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    """
    Handle selection of balance top-up amount.

    Prompts for a custom amount if selected, otherwise proceeds to payment options.

    Args:
        callback (CallbackQuery): The incoming callback query.
        state (FSMContext): Finite state machine context for storing data.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = callback.from_user.id

    try:
        user_info = await services.get_user_info(user_id)
        if user_info is None:
            text = i18n.error.user_not_found()
            await callback.message.edit_text(text=text)
            await callback.answer()
            return

        await state.set_state(PaymentSG.add_balance)
        state_data = await state.get_data()
        balance = state_data.get("balance", 0)
        days_left = user_info.get('durations', (0, 0, 0))

        await state.update_data(
            payment_type="add_balance",
            device_type="balance",
            period=0
        )
        _, _, amount = callback.data.split("_")

        # logger.info(f"User {user_id} adding balance: {amount}")
        
        if amount == "custom":
            await state.set_state(PaymentSG.custom_balance)
            await callback.message.edit_text(text=i18n.fill.custom.balance(), 
                                             reply_markup=payment_kb.decline_custom_payment(i18n))
        else:
            await state.update_data(amount=int(amount))
            keyboard = payment_kb.payment_select(i18n, payment_type="add_balance")
            text = i18n.topup.balance.menu(
                    balance=balance, 
                    days=max(days_left),
                    amount=amount
                    )
            await callback.message.edit_text(text=text, reply_markup=keyboard)

        await callback.answer()

    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.telegram_failed())
        await callback.answer()
    except ValueError as e:
        logger.error(f"Invalid amount for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.invalid_amount())
        await callback.answer()
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.unexpected())
        await callback.answer()

@payment_router.message(PaymentSG.custom_balance)
async def custom_balance_handler(
    message: Message,
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    """
    Handle custom balance top-up amount input.

    Validates the amount and proceeds to payment options.

    Args:
        message (Message): The incoming message with custom amount.
        state (FSMContext): Finite state machine context for storing data.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = message.from_user.id
    payment_type = "add_balance"
    logger.info(f"User {user_id} entered custom balance")

    try:
        user_info = await services.get_user_info(user_id)
        if user_info is None:
            text = i18n.error.user_not_found()
            await message.answer(text=text)
            return

        amount = message.text.strip()
        try:
            amount = int(amount)
            if amount <= 49:
                raise ValueError("Amount must be positive and above 49")
        except ValueError:
            await message.answer(text=i18n.error.invalid_amount())
            return

        state_data = await state.get_data()
        balance = state_data.get("balance", 0)
        days_left = user_info.get('durations', (0, 0, 0))

        await state.update_data(
            amount=amount,
            payment_type=payment_type,
            device_type="balance"
            )
        keyboard = payment_kb.payment_select(i18n, payment_type=payment_type)
        text = i18n.topup.balance.menu(balance=balance, days=max(days_left), amount=amount)
        await message.answer(text=text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@payment_router.callback_query(PaymentSG.buy_subscription, F.data.startswith("payment_"))
async def buy_subscription_handler(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    i18n: TranslatorRunner
) -> None:
    """
    Handle payment method selection and initiate payment.

    Supports ukassa, crypto, balance, and Telegram Stars payment methods.

    Args:
        callback (CallbackQuery): The incoming callback query with payment method.
        state (FSMContext): Finite state machine context for storing data.
        bot (Bot): Aiogram Bot instance for sending invoices.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = callback.from_user.id
    logger.info(f"User {user_id} initiating payment")

    try:
        state_data = await state.get_data()
        payment_type = state_data.get("payment_type", "add_balance")
        amount = state_data.get("amount")
        balance = state_data.get("balance")
        device_type = state_data.get("device_type")
        period = state_data.get("period", "0")
        device = state_data.get("device")

        # logger.info(f'Payment type: {payment_type}; device: {device}; amount: {amount}; balance: {balance}; device type: {device_type}; period: {period}')
        
        # For subscriptions, calculate amount from month_price
        if payment_type == "buy_subscription":

            if device in ('5', '10'):
                amount = services.MONTH_PRICE[device_type][device][str(period)]
            else:
                amount = services.MONTH_PRICE[device_type][str(period)]

            if not (period and device_type):
                await callback.message.edit_text(text=i18n.error.invalid_payment_data())
                await callback.answer()
                return
            if amount is None:
                await callback.message.edit_text(text=i18n.error.invalid_payment_data())
                await callback.answer()
                return
   
        if amount is None:
            await callback.message.edit_text(text=i18n.error.invalid_amount())
            await callback.answer()
            return

        _, method = callback.data.split("_")
        payload = f"{user_id}:{amount}:{period}:{device_type}:{device}:{payment_type}:{method}"

        # UKASSA BUY SUBSCRIPTION
        if method == "ukassa":
            contact = await user_req.get_user(user_id)
            if contact is None:
                await callback.message.answer(text=i18n.error.user_not_found())
                await callback.answer()
                return

            email = contact.get('email_address', None)
            phone = contact.get('phone_number', None)
            await state.update_data(amount=amount, payload=payload, payment_type=payment_type)
            keyboard = payment_kb.contact_select_kb(i18n=i18n, email=email, phone=phone)

            email = email if email is not None else i18n.no.contact()
            phone = phone if phone is not None else i18n.no.contact()

            text = i18n.select.contact(email=email, phone=phone)
            await callback.message.answer(text=text, reply_markup=keyboard)
            await callback.answer()

        # CRYPTOBOT BUY SUBSCRIPTION
        elif method == "crypto":
            asset = 'TON'
            rate = await payment_req.exchange_rate(asset)
            rated_amount = amount / rate
            result = await payment_req.create_cryptobot_invoice(rated_amount, asset, payload)
            if result is not None:
                invoice_url, invoice_id = result
                await state.update_data(invoice_id=invoice_id)
                await payment_req.save_invoice(user_id, invoice_id, rated_amount, asset, payload)
                await callback.message.edit_text(text=i18n.invoice(
                        invoice_url=invoice_url, 
                        invoice_id=invoice_id))
            else:
                logger.error(f"Unexpected error for user {user_id} in buy subscription by cryptobot")
                await callback.message.edit_text(text=i18n.error.unexpected())
                await callback.answer()
                return

        # BALANCE BUY SUBSCRIPTION
        elif method == "balance":
            if amount > balance:
                await callback.message.edit_text(text=i18n.notenough.balance())
                await callback.answer()
                return
            else:
                result = await payment_req.payment_balance_process(
                        user_id, amount, period, device_type, device, payment_type, method)
                if result is not None:
                    if device not in ('5', '10'):
                        await state.set_state(DevicesSG.device_name)
                        await callback.message.answer(
                                text=i18n.buy.subscription.success(balance=(balance-amount)),
                                reply_markup=main_kb.back_to_devices_inline_kb(i18n))
                    else:
                        await state.clear()
                        await state.set_state(PaymentSG.add_device)
                        await callback.message.answer(
                                text=i18n.buy.subscription.success.combo(),
                                reply_markup=main_kb.back_to_devices_inline_kb(i18n))
                else:
                    logger.error(f"Unexpected error for user {user_id} in buy subscription by balance")
                    await callback.message.edit_text(text=i18n.error.unexpected())
                    await callback.answer()
                    return

        # TELEGRAM STARS BUY SUBSCRIPTION
        elif method == "stars":
            device_stars = MONTH_PRICE_STARS.get(device_type, {})

            if device_type == 'combo' and device in ('5', '10'):
                stars_amount =  device_stars[device][str(period)]
            elif device_type in ('device', 'router'):
                stars_amount = device_stars[str(period)]
            else:
                await callback.message.edit_text(text=i18n.error.unexpected())
                await callback.answer()
                return
                
            await bot.send_invoice(
                chat_id=callback.message.chat.id,
                title=i18n.stars.subscription.title(),
                description=i18n.stars.subscription.description(amount=amount),
                payload=payload,
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(label=i18n.payment.label(), amount=stars_amount)],
                start_parameter=payment_type
            )
        else:
            await callback.message.edit_text(text=i18n.error.invalid_payment_method())
            await callback.answer()
            return

        # Clear state only after successful initiation
        # if method != "stars" or method != "balance":  # Stars payment requires state until completion
        #    await state.clear()
        await callback.answer()

    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.telegram_failed())
        await callback.answer()
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.unexpected())
        await callback.answer()

@payment_router.callback_query(
        StateFilter(PaymentSG.add_balance), 
        F.data.startswith("payment_"))
async def add_balance_handler(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    i18n: TranslatorRunner
) -> None:
    """
    Handle payment method selection and initiate payment.

    Supports ukassa, crypto, balance, and Telegram Stars payment methods.

    Args:
        callback (CallbackQuery): The incoming callback query with payment method.
        state (FSMContext): Finite state machine context for storing data.
        bot (Bot): Aiogram Bot instance for sending invoices.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = callback.from_user.id
    logger.info(f"User {user_id} initiating payment")

    try:
        state_data = await state.get_data()
        payment_type = state_data.get("payment_type", "add_balance")
        amount = state_data.get("amount")
        device_type = state_data.get("device_type", "balance")
        device = state_data.get("device", "balance")
        period = state_data.get("period", "0")
        
        if amount is None:
            await callback.message.edit_text(text=i18n.error.invalid_amount())
            await callback.answer()
            return

        _, method = callback.data.split("_")
        payload = f"{user_id}:{amount}:{period}:{device_type}:{device}:{payment_type}:{method}"
        
        # UKASSA ADD BALANCE
        if method == "ukassa":
            contact = await user_req.get_user(user_id)
            if contact is None:
                await callback.message.answer(text=i18n.error.user_not_found())
                await callback.answer()
                return
            email = contact.get('email_address', None)
            phone = contact.get('phone_number', None)
            await state.update_data(amount=amount, payload=payload, payment_type=payment_type)
            keyboard = payment_kb.contact_select_kb(i18n=i18n, email=email, phone=phone)

            email = email if email is not None else i18n.no.contact()
            phone = phone if phone is not None else i18n.no.contact()

            text = i18n.select.contact(email=email, phone=phone)
            await callback.message.answer(text=text, reply_markup=keyboard)
            await callback.answer()

        # CRYPTOBOT ADD BALANCE
        elif method == "crypto":
            asset = 'TON'
            rate = await payment_req.exchange_rate(asset)
            rated_amount = amount / rate
            result = await payment_req.create_cryptobot_invoice(rated_amount, asset, payload)
            if result is not None:
                invoice_url, invoice_id = result
                await state.update_data(invoice_id=invoice_id)
                await payment_req.save_invoice(user_id, invoice_id, rated_amount, asset, payload)
                await callback.message.edit_text(text=i18n.invoice(
                        invoice_url=invoice_url, 
                        invoice_id=invoice_id))
            else:
                logger.error(f"Unexpected error for user {user_id} in buy subscription by cryptobot")
                await callback.message.edit_text(text=i18n.error.unexpected())
                await callback.answer()
                return

        # TELEGRAM STARS ADD BALANCE
        elif method == "stars":
            stars_amount = int(amount / START_PRICE)
            await bot.send_invoice(
                chat_id=callback.message.chat.id,
                title=i18n.stars.subscription.title(),
                description=i18n.stars.subscription.description(amount=amount),
                payload=payload,
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice(label=i18n.payment.label(), amount=stars_amount)],
                start_parameter=payment_type
            )
        else:
            await callback.message.edit_text(text=i18n.error.invalid_payment_method())
            await callback.answer()
            return

        # Clear state only after successful initiation
        if method != "stars":  # Stars payment requires state until completion
            await state.set_state(None)

        await callback.answer()

    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.telegram_failed())
        await callback.answer()
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.unexpected())
        await callback.answer()

@payment_router.callback_query(F.data.startswith('add_contact_'))
async def add_contact_type_handler(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    user_id = callback.from_user.id
    contact_type = callback.data.split('_')[-1]  # 'email' или 'phone'
    
    logger.info(f"User {user_id} started adding contact: {contact_type}")
    
    try:
        if contact_type == 'email':
            await state.set_state(PaymentSG.add_email)
            await callback.message.edit_text(text=i18n.fill.email())
            await callback.answer()
        elif contact_type == 'phone':

            await callback.message.answer(
                text=i18n.fill.phone(),
                reply_markup=payment_kb.get_phone_kb(i18n)
            )
            await callback.answer()
        else:
            logger.error(f"Invalid contact_type: {contact_type}")
            await callback.message.edit_text(text=i18n.error.unexpected())
            await callback.answer()
    
    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.telegram_failed())
        await callback.answer()
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.unexpected())
        await callback.answer()

@payment_router.message(StateFilter(PaymentSG.add_email))
async def email_handler(
    message: Message,
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    user_id = message.from_user.id
    email = message.text.strip()

    EMAIL_REGEX = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(EMAIL_REGEX, email):
        logger.info(f"Invalid email format for user {user_id}: {email}")
        await message.answer(text=i18n.error.wrong.email())
        return
    try:
        result = await user_req.update_user_contact(
            user_id=user_id, contact_type='email', contact=email)
        user = await user_req.get_user(user_id)
        # logger.info(user)
        
        if not isinstance(result, dict) or user is None:
            logger.error(f"Invalid response from update_user_contact for user {user_id}")
            await message.answer(text=i18n.error.unexpected())
            return
       
        # logger.info(f"User {user_id} saved email: {email}")
        email = user.get('email_address', None)
        phone = user.get('phone_number', None)
        
        await state.set_state(None)  # Сбрасываем состояние, сохраняя state_data
        
        keyboard = payment_kb.contact_select_kb(i18n=i18n, email=email, phone=phone)

        email = email if email is not None else i18n.no.contact()
        phone = phone if phone is not None else i18n.no.contact()

        text = i18n.select.contact(email=email, phone=phone)
        await message.delete()  # Удаляем сообщение с email
        await message.answer(text=text, reply_markup=keyboard)
    
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@payment_router.message(F.content_type == 'contact')
async def phone_handler(
    message: Message,
    i18n: TranslatorRunner
) -> None:
    user_id = message.from_user.id
    contact = message.contact
    
    if contact is None:
        await message.answer(text=i18n.error.no.number())
        return
    
    phone = contact.phone_number
    try:
        result = await user_req.update_user_contact(
            user_id=user_id, contact_type='phone', contact=phone)
        
        user = await user_req.get_user(user_id)
        # jlogger.info(user)
        
        if not isinstance(result, dict) or user is None:
            logger.error(f"Invalid response from update_user_contact for user {user_id}")
            await message.answer(text=i18n.error.unexpected())
            return
       
        email = user.get('email_address', None)
        phone = user.get('phone_number', None)
        
        # logger.info(f"User {user_id} saved phone: {result.get('phone_number')}")
        keyboard = payment_kb.contact_select_kb(i18n=i18n, email=email, phone=phone)

        email = email if email is not None else i18n.no.contact()
        phone = phone if phone is not None else i18n.no.contact()

        text = i18n.select.contact(email=email, phone=phone)
        await message.answer(text=text, reply_markup=keyboard)
    
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@payment_router.callback_query(F.data.startswith('contact_'))
async def process_ukassa_handler(
    callback: CallbackQuery,
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    user_id = callback.from_user.id
    contact_type = callback.data.split('_')[-1]  # 'email' или 'phone'
    first_name = callback.from_user.first_name
    last_name = callback.from_user.last_name or ''
    username = callback.from_user.username or "User"
    customer = first_name if first_name else username
    customer = f"{customer} {last_name}".strip()

    try:
        state_data = await state.get_data()
        payment_type = state_data.get("payment_type")
        amount = state_data.get("amount")

        device_type = state_data.get("device_type")
        period = state_data.get("period")
        device = state_data.get("device")
        # logger.info(f'\nUPDATE STATE\nAMOUNT {amount}\nPAYMENT_TYPE {payment_type}')       
        if not amount or not payment_type:
            await callback.message.answer(text=i18n.error.invalid_payment_data())
            await callback.answer()
            return

        contact = await user_req.get_user(user_id)
        # logger.info(f'USER: {contact}')
        if contact is None:
            await callback.message.answer(text=i18n.error.no.contact())
            await callback.answer()
            return

        customer_data = {"full_name": customer}
        if contact_type == "email" and contact.get("email_address"):
            customer_data["email"] = contact["email_address"]
        elif contact_type == "phone" and contact.get("phone_number"):
            customer_data["phone"] = contact["phone_number"]
        else:
            await callback.message.edit_text(text=i18n.error.no.contact())
            await callback.answer()
            return

        # logger.info(f"Payment type: {payment_type}; device: {device}; amount: {amount}; "
        #           f"balance: {balance}; device_type: {device_type}; period: {period}; "
        #           f"customer: {customer}; contact: {customer_data}")
        payload = f"{user_id}:{amount}:{period}:{device_type}:{device}:{payment_type}:ukassa"

        result = await payment_req.create_ukassa_invoice(
            amount=10,
            currency="RUB",
            payload=payload,
            i18n=i18n,
            customer=customer_data,
            description=i18n.ukassa.subscription.description(amount=amount)
        )
        if result:
            invoice_url, invoice_id = result
            await state.update_data(invoice_id=invoice_id)
            await payment_req.save_invoice(
                user_id=user_id,
                invoice_id=invoice_id,
                amount=amount,
                currency="RUB",
                payload=payload
            )
            # logger.info(f"Invoice created for user {user_id}: ID={invoice_id}, URL={invoice_url}")
            await callback.message.answer(
                text=i18n.invoice(invoice_url=invoice_url, invoice_id=invoice_id),
                reply_markup=payment_kb.pay_inline(i18n, invoice_url)
            )
            await state.set_state(None)  # Сбрасываем состояние
            await callback.answer()
        else:
            logger.error(f"Failed to create invoice for user {user_id}. result: {result}")
            await callback.message.answer(text=i18n.error.payment_failed())
            await callback.answer()

    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.telegram_failed())
        await callback.answer()
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.unexpected())
        await callback.answer()

@payment_router.pre_checkout_query()
async def pre_checkout(
    pre_checkout_query: PreCheckoutQuery,
    bot: Bot
) -> None:
    """
    Handle pre-checkout queries for Telegram Stars payments.

    Confirms the payment to proceed.

    Args:
        pre_checkout_query (PreCheckoutQuery): The incoming pre-checkout query.
        bot (Bot): Aiogram Bot instance for responding to queries.

    Returns:
        None
    """
    try:
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)
    except Exception as e:
        logger.error(f"Failed to process pre-checkout for query {pre_checkout_query.id}: {e}")
        await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=False, error_message="Payment failed")

@payment_router.message(F.content_type == "successful_payment")
async def process_payment(
    message: Message,
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    """
    Handle successful Telegram Stars payments.

    Notifies the user and clears the state.

    Args:
        message (Message): The incoming message with payment details.
        state (FSMContext): Finite state machine context for clearing data.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = message.from_user.id
    user_data = await services.get_user_data(user_id)
    if user_data is None:
        await message.answer(text=i18n.error.unexpected())
        return

    balance = user_data.get('balance', 0)
    logger.info(f"Successful payment for user {user_id}")

    try:
        payment = message.successful_payment
        # logger.info(payment.invoice_payload)
        user_id, amount, period, device_type, device, payment_type, method = payment.invoice_payload.split(':')
        result = await payment_req.payment_balance_process(user_id, amount, period, device_type, device, payment_type, method)
        if result is not None:
            if device == 'balance':
                    await message.answer(
                        i18n.promo.success.balance(),
                        reply_markup=main_kb.back_inline_kb(i18n)
                    )

            elif device not in ('5', '10'):
                await state.set_state(DevicesSG.device_name)
                await message.answer(
                        text=i18n.buy.subscription.success(balance=(int(balance))),
                        reply_markup=main_kb.back_inline_kb(i18n))
            else:
                await state.clear()
                await message.answer(
                        text=i18n.buy.subscription.success.combo(),
                        reply_markup=main_kb.back_inline_kb(i18n)
                        )
        else:
            logger.error(f"Unexpected error for user {user_id} in buy subscription by balance")
            await message.answer(text=i18n.error.unexpected())
            return

    except Exception as e:
        logger.error(f"Failed to process payment for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())
