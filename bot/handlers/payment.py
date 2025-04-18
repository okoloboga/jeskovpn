import logging
from typing import Union
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, LabeledPrice, PreCheckoutQuery
from fluentogram import TranslatorRunner

from services import services, payment_req
from services.services import day_price
from services.states import PaymentSG
from keyboards import payment_kb

payment_router = Router()

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s'
)


@payment_router.message(F.text.startswith("Баланс") | F.text.startswith("Balance") | 
                        F.text.in_(['Пополнить баланс', 'Add balnce']))
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
        if user_data is None:
            text = i18n.error.user_not_found()
            if isinstance(event, CallbackQuery):
                await event.message.edit_text(text=text)
                await event.answer()
            else:
                await event.answer(text=text)
            return

        balance = user_data["balance"]
        day_price = await services.day_price(user_id)
        await state.update_data(
                balance=balance, 
                day_price=day_price
                )

        keyboard = payment_kb.add_balance_kb(i18n)
        text = i18n.balance.menu(
                balance=balance, 
                days = 0 if day_price == 0 else (int(balance/day_price))
                )

        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text=text, reply_markup=keyboard)
            await event.answer()
        else:
            await event.answer(text=text, reply_markup=keyboard)

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
async def add_balance_handler(
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
        state_data = await state.get_data()
        balance = state_data.get("balance", 0)
        day_price = state_data.get("day_price", 0)

        await state.update_data(
            payment_type="add_balance",
            device_type="balance"
        )
        _, _, amount = callback.data.split("_")

        logger.info(f"User {user_id} adding balance: {amount}")
        
        if amount == "custom":
            await state.set_state(PaymentSG.custom_balance)
            await callback.message.edit_text(text=i18n.fill.custom.balance(), 
                                             reply_markup=payment_kb.decline_custom_payment(i18n))
        else:
            await state.update_data(amount=int(amount))
            keyboard = payment_kb.payment_select(i18n, payment_type="add_balance")
            text = i18n.payment.menu(
                    balance=balance, 
                    days = 0 if day_price == 0 else int(balance / day_price),
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
        amount = message.text.strip()
        try:
            amount = int(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError:
            await message.answer(text=i18n.error.invalid_amount())
            return

        state_data = await state.get_data()
        balance = state_data.get("balance", 0)
        day_price = state_data.get("day_price", 0)
        days = 0 if day_price == 0 else int(balance/day_price)

        await state.update_data(
            amount=amount,
            payment_type=payment_type,
            device_type="balance"
            )
        keyboard = payment_kb.payment_select(i18n, payment_type=payment_type)
        text = i18n.payment.menu(balance=balance, days=days, amount=amount)
        await message.answer(text=text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@payment_router.callback_query(F.data.startswith("payment_"))
async def payment_handler(
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

        # For subscriptions, calculate amount from month_price
        if payment_type == "buy_subscription":
            period = state_data.get("period")
            device_type = state_data.get("device_type")
            if not (period and device_type):
                await callback.message.edit_text(text=i18n.error.invalid_payment_data())
                await callback.answer()
                return
            amount = services.MONTH_PRICE.get(device_type, {}).get(period)
            if amount is None:
                await callback.message.edit_text(text=i18n.error.invalid_payment_data())
                await callback.answer()
                return

        if amount is None:
            await callback.message.edit_text(text=i18n.error.invalid_amount())
            await callback.answer()
            return

        _, method = callback.data.split("_")

        if method == "ukassa":
            await payment_req.payment_ukassa_process(user_id, amount, period, device_type, payment_type)
            await callback.message.edit_text(text=i18n.payment.pending())
        elif method == "crypto":
            await payment_req.payment_crypto_process(user_id, amount, period, device_type, payment_type)
            await callback.message.edit_text(text=i18n.payment.pending())
        elif method == "balance":
            await payment_req.payment_balance_process(user_id, amount, period, device_type, payment_type)
            await callback.message.edit_text(text=i18n.payment.success())
        elif method == "stars":
            # Convert rubles to Telegram Stars (approx. 1 RUB = 1 Star)
            stars_amount = amount
            await bot.send_invoice(
                chat_id=callback.message.chat.id,
                title=i18n.stars.subscription.title(),
                description=i18n.stars.subscription.description(),
                payload=f"{payment_type}:{user_id}:{amount}",
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
            await state.clear()

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
    logger.info(f"Successful payment for user {user_id}")

    try:
        payment = message.successful_payment
        payload = payment.invoice_payload
        # Example payload: "buy_subscription:12345:900"
        payment_type, _, amount = payload.split(":")
        await message.answer(
            text=i18n.stars.payment.successful(payload=payment_type, amount=amount)
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Failed to process payment for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())
