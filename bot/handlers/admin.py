import logging
from typing import Optional
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from fluentogram import TranslatorRunner

from services import admin_req
from services.states import AdminSG
from keyboards import admin_kb
from config import get_config, Admin

admin_router = Router()
admin = get_config(Admin, "admin")
admin_id = admin.id

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s:%(lineno)d #%(levelname)-8s "
           "[%(asctime)s] - %(name)s - %(message)s"
)

@admin_router.callback_query(F.data.startswith("reply_ticket_"))
async def reply_ticket_start(
    callback: CallbackQuery,
    i18n: TranslatorRunner,
    state: FSMContext
) -> None:
    """
    Handle admin's request to reply to a support ticket.

    Checks admin privileges, sets FSM state, and prompts for a reply.

    Args:
        callback (CallbackQuery): The incoming callback query with ticket data.
        i18n (TranslatorRunner): Translator for localized responses.
        state (FSMContext): Finite state machine context for storing user ID.

    Returns:
        None
    """
    user_id = callback.from_user.id
    logger.info(f"User {user_id} attempting to reply to a ticket")

    try:
        if user_id != admin_id:
            await callback.answer(text=i18n.error.only.admin(), show_alert=True)
            return

        ticket_user_id = int(callback.data.split("_")[2])
        await state.update_data(user_id=ticket_user_id)
        await state.set_state(AdminSG.reply_ticket)

        await callback.message.edit_text(
            text=i18n.reply.ticket(),
            reply_markup=admin_kb.cancel_reply_kb(i18n)
        )
        await callback.answer()

    except ValueError as e:
        logger.error(f"Invalid ticket data for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.invalid_data())
        await callback.answer()
    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.telegram_failed())
        await callback.answer()
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await callback.message.edit_text(text=i18n.error.unexpected())
        await callback.answer()

@admin_router.message(AdminSG.reply_ticket)
async def process_ticket_reply(
    message: Message,
    bot: Bot,
    state: FSMContext,
    i18n: TranslatorRunner
) -> None:
    """
    Process admin's reply to a support ticket.

    Sends the reply to the user, deletes the ticket, and notifies the admin.

    Args:
        message (Message): The incoming message with reply text.
        bot (Bot): Aiogram Bot instance for sending messages.
        state (FSMContext): Finite state machine context for retrieving user ID.
        i18n (TranslatorRunner): Translator for localized responses.

    Returns:
        None
    """
    user_id = message.from_user.id
    logger.info(f"User {user_id} processing ticket reply")

    try:
        if user_id != admin_id:
            await message.answer(text=i18n.error.only.admin())
            return

        reply_text = message.text
        data = await state.get_data()
        ticket_user_id = data.get("user_id")

        if not ticket_user_id:
            await message.answer(text=i18n.error.invalid_data())
            await state.clear()
            return

        await bot.send_message(
            chat_id=ticket_user_id,
            text=i18n.ticket.answer(reply_text=reply_text)
        )
        await admin_req.delete_ticket(ticket_user_id)
        await message.answer(
            text=i18n.admin.answer(),
            reply_markup=admin_kb.admin_menu_kb(i18n)
        )
        await state.clear()

    except TelegramBadRequest as e:
        logger.error(f"Telegram API error for user {user_id}: {e}")
        await message.answer(text=i18n.error.telegram_failed())
        await state.clear()
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer(text=i18n.error.unexpected())
        await state.clear()
