import logging
from typing import Optional
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.utils.deep_linking import create_start_link
from aiogram.types import Message
from fluentogram import TranslatorRunner

from services import user_req
from services.states import SupportSG
from keyboards import another_kb, main_kb
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

async def get_user_data(user_id: int) -> Optional[dict]:
    """
    Fetch user data from the service.

    Args:
        user_id (int): Telegram user ID.

    Returns:
        Optional[dict]: User data with balance and subscription status, or None if not found.

    Raises:
        Exception: If the service request fails.
    """
    try:
        user = await user_req.get_user(user_id)
        if user is None:
            logger.warning(f"User {user_id} not found")
            return None
        return {
            "balance": getattr(user, "balance", 0),
            "is_subscribed": getattr(user, "is_subscribed", False)
        }
    except Exception as e:
        logger.error(f"Failed to fetch user {user_id}: {e}")
        raise

@another_router.message(F.text.statrtswith("До окончания подписки") | F.text.statrtswith("Until subscription end") | 
                        F.text.in_(["Нет активной подписки", "No active subscription"]))
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
        user_data = await get_user_data(user_id)
        if user_data is None:
            await message.answer(text=i18n.error.user_not_found())
            return

        balance = user_data["balance"]
        is_subscribed = user_data["is_subscribed"]
        min_subscription_price = 149  # Minimum price for "device" for 1 month

        if is_subscribed:
            text = i18n.subscription.menu.active(name=name, balance=balance)
        elif balance >= min_subscription_price:
            text = i18n.nosubscription.have.balance(balance=balance)
        else:
            text = i18n.nosubscription.nobalance(balance=balance)

        keyboard = another_kb.subscription_menu(i18n)
        await message.answer(text=text, reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@another_router.message(F.text.in_(["Тех. Поддержка", "Support"]))
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
    logger.info(f"User {user_id} accessing на русском языке: Показ меню поддержки для пользователя {user_id}")

    try:
        ticket_data = await user_req.get_ticket_by_id(user_id)
        ticket_content = ticket_data.get("content") if ticket_data else None
        ticket_text = i18n.noticket() if ticket_content is None else str(ticket_content)

        await state.set_state(SupportSG.create_ticket)
        keyboard = main_kb.back_inline_kb(i18n)
        await message.answer(text=i18n.ticket.menu(ticket=ticket_text), reply_markup=keyboard)

    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@another_router.message(SupportSG.create_ticket)
async def ticket_handler(
    message: Message,
    bot: Bot,
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    """
    Handle support ticket creation.

    Sends the ticket to the admin and notifies the user.

    Args:
        message (Message): The incoming message with ticket content.
        bot (Bot): Aiogram Bot instance for sending messages.
        state (FSMContext): Finite state machine context for clearing state.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = message.from_user.id
    username = message.from_user.username or "Unknown"
    content = message.text
    logger.info(f"User {user_id} creating support ticket")

    try:
        await user_req.send_ticket(content, user_id, username)
        await bot.send_message(
            chat_id=admin_id,
            text=f"#{user_id}\n@{username}:\n\n{content}",
            reply_markup=another_kb.reply_keyboard(i18n, user_id)
        )
        await message.answer(
            text=i18n.ticket.sended(),
            reply_markup=main_kb.main_kb(
                i18n=i18n,
                is_subscribed=False,  # Fetch actual data if needed
                subscription_expires="",
                balance=0,
                user_language="RU"  # Adjust based on user preference
            )
        )
        await state.clear()

    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await message.answer(text=i18n.error.telegram_failed())
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())

@another_router.message(F.text.in_(["Пригласить друга", "Invite Friend"]))
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
