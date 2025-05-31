import logging
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link
from aiogram.types import Message, CallbackQuery
from fluentogram import TranslatorRunner
from datetime import datetime

from services import services, raffle_req, user_req
from keyboards import another_kb, main_kb, raffle_kb, payment_kb, devices_kb
from config import get_config, Admin

another_router = Router()
admin = get_config(Admin, "admin")  # Admin configuration
admin_id = admin.id

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s:%(lineno)d #%(levelname)-8s "
           "[%(asctime)s] - %(name)s - %(message)s"
)

@another_router.message(F.text.startswith("До окончания") | F.text.startswith("Until")) 
@another_router.message(F.text.in_(["Нет активной подписки 😔", "No active subscription 😔"]))
async def subscription_handler(
    message: Message,
    i18n: TranslatorRunner
) -> None:
    """
    Handle subscription menu requests.

    Displays subscription status and balance, with options based on user data.

    Args:
        message (Message): The incoming message with subscription command.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = message.from_user.id
    name = message.from_user.first_name or message.from_user.username or "User"
    logger.info(f"Showing subscription menu for user {user_id}")

    try:
        user_data = await services.get_user_data(user_id)
        if user_data is None:
            await message.answer(text=i18n.error.user_not_found())
            return

        balance = user_data["balance"]
        user_info = await services.get_user_info(user_id)

        if user_info is None:
            await message.answer(text=i18n.error.unexpected())
            return

        days_left = user_info.get('durations', (0, 0, 0))
        is_subscribed = user_info.get('is_subscribed', False)
        devices = user_info.get('total_devices', 0)
        min_subscription_price = 100

        if is_subscribed:
            text = i18n.subscription.menu.active(
                    name=name, 
                    balance=balance, 
                    days=max(days_left),
                    devices=devices
                    )
        elif balance >= min_subscription_price:
            text = i18n.nosubscription.have.balance(balance=balance)
        else:
            text = i18n.nosubscription.nobalance(balance=balance)

        keyboard = another_kb.subscription_menu(i18n)
        await message.answer(text=text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@another_router.message(F.text == 'Подписка активна, устройств нет  🕒')
async def no_active_devices(
    message: Message,
    i18n: TranslatorRunner
) -> None:
    await message.answer(
            text=i18n.noactive.devices(),
            reply_markup=devices_kb.back_device_kb(i18n)
            )

@another_router.message(F.text == '/privacy')
async def privacy_handler(
    message: Message,
    i18n: TranslatorRunner
) -> None:
    await message.answer(text=i18n.privacy())

@another_router.message(F.text.in_(["Тех. Поддержка 🛠️", "Tech Support 🛠️"]))
async def support_handler(
    message: Message,
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    """
    Handle support menu requests.

    Displays the current support ticket, if any, and prompts for a new ticket.

    Args:
        message (Message): The incoming message with support command.
        state (FSMContext): Finite state machine context for ticket creation.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = message.from_user.id
    try:
        keyboard = main_kb.back_inline_kb(i18n)
        await message.answer(text=i18n.ticket.menu(), reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@another_router.message(F.text.in_(["/friends", "Пригласить друга 👥", "Invite a Friend 👥"]))
async def referral_handler(
    message: Message,
    bot: Bot,
    i18n: TranslatorRunner
) -> None:
    """
    Handle referral link requests.

    Generates and sends a referral link to the user.

    Args:
        message (Message): The incoming message with referral command.
        bot (Bot): Aiogram Bot instance for creating links.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = message.from_user.id
    logger.info(f"Generating referral link for user {user_id}")

    try:
        link = await create_start_link(bot, str(user_id), encode=True)
        keyboard = main_kb.back_kb(i18n)
        await message.answer(text=i18n.referral.link(link=link), reply_markup=keyboard)
    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await message.answer(text=i18n.error.telegram_failed())
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@another_router.message(F.text == "/gift")
async def cmd_gift(
        message: Message, 
        i18n: TranslatorRunner
) -> None:
    try:
        user_id = message.from_user.id
        raffles = await raffle_req.get_active_raffles()
        if not raffles:
            await message.answer(i18n.no.active.raffles())
            return
        
        for raffle in raffles:
            ticket_data = await raffle_req.get_user_tickets(raffle_id=raffle["id"], user_id=user_id)
            ticket_count = ticket_data.get("count", 0) if ticket_data else 0
            start_date = datetime.fromisoformat(raffle["start_date"]).strftime("%Y-%m-%d %H:%M")
            end_date = datetime.fromisoformat(raffle["end_date"]).strftime("%Y-%m-%d %H:%M")
            ticket_price = f"{raffle['ticket_price']}" if raffle.get("ticket_price") else i18n.forsubscription()

            text = i18n.raffle.info(
                name=raffle["name"],
                start_date=start_date,
                end_date=end_date,
                ticket_price=ticket_price,
                ticket_count=ticket_count
            )
            images = raffle.get("images", [])
            if images:
                await message.answer_photo(
                    photo=images[0],
                    caption=text,
                    reply_markup=raffle_kb.raffle_menu_kb(raffle["id"], raffle["type"], i18n)
                )
            else:
                await message.answer(
                    text=text,
                    reply_markup=raffle_kb.raffle_menu_kb(raffle["id"], raffle["type"], i18n)
                )
    except Exception as e:
        logger.error(f"Error in cmd_gift: {e}")
        await message.answer(i18n.error())

@another_router.callback_query(F.data.startswith("raffle_buy_tickets_"))
async def process_buy_tickets(
        callback: CallbackQuery, 
        state: FSMContext, 
        i18n: TranslatorRunner
) -> None:
    try:
        raffle_id = int(callback.data.split("_")[-1])
        await callback.message.answer(
            i18n.enter.ticket.count(),
            reply_markup=raffle_kb.ticket_purchase_kb(i18n)
        )
        await state.update_data(raffle_id=raffle_id)
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in process_buy_tickets: {e}")
        await callback.message.answer(i18n.error())
        await callback.answer()

@another_router.callback_query(F.data.startswith("ticket_count_"))
async def process_ticket_count(
        callback: CallbackQuery, 
        state: FSMContext, 
        i18n: TranslatorRunner
) -> None:
    try:
        _, _, count = callback.data.split('_')
        if int(count) <= 0:
            await callback.message.answer(i18n.error.invalid.ticket.count())
            return
        
        data = await state.get_data()
        raffle_id = data["raffle_id"]

        raffle = await raffle_req.get_active_raffles(raffle_id=raffle_id)
        if not raffle:
            await callback.message.answer(i18n.error.raffle.notfound())
            await state.clear()
            return

        if raffle["type"] != "ticket":
            await callback.message.answer(i18n.error.cannot.buy.tickets())
            await state.clear()
            return
        
        ticket_price = raffle["ticket_price"]       
        amount = float(count) * float(ticket_price)
        user_id = callback.from_user.id      
        # Создание инвойса через ЮKassa
        payload = f"{user_id}:{amount}:0:ticket:{raffle_id}:ticket:ukassa"
        
        contact = await user_req.get_user(user_id)
       
        if contact is None:
            await callback.message.answer(text=i18n.error.user_not_found())
            await callback.answer()
            return
        email = contact.get('email_address', None)
        phone = contact.get('phone_number', None)
        await state.update_data(
                amount=amount, 
                payload=payload, 
                payment_type='ticket')
        keyboard = payment_kb.contact_select_kb(i18n=i18n, email=email, phone=phone)

        email = email if email is not None else i18n.no.contact()
        phone = phone if phone is not None else i18n.no.contact()

        text = i18n.select.contact(email=email, phone=phone)

        logger.info(f'\n\nPAYLOAD: {payload}')

        await callback.message.answer(text=text, reply_markup=keyboard)
        await callback.answer()

    except ValueError:
        await callback.message.answer(i18n.error.invalid.ticket.count())
    except Exception as e:
        logger.error(f"Error in process_ticket_count: {e}")
        await callback.message.answer(i18n.error())
        await state.clear()
