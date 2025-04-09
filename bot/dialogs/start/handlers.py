import logging

from aiogram import Router, Bot
from aiogram.utils.deep_linking import decode_payload
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button

from fluentogram import TranslatorRunner

from states import MainSG, StartSG
from services import 


start_router = Router()

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')

# Process START CommandStart
@start_router.message(CommandStart(deep_link_encoded=True))
async def command_start_getter(message: Message,
                               dialog_manager: DialogManager,
                               command: CommandObject):
    
    user_id = message.from_user.id
    session: AsyncSession = dialog_manager.middleware_data.get('session')
    logger.info(f'Referral data: {command}')

    # If user start bot by referral link 
    if command.args:
        logger.info(f'CommandObject is {command}')
        args = command.args
        payload = decode_payload(args)
    else:
        payload = None

    user = await get_user(session, user_id)
    logger.info(f'User from database {user}')

    # If user new - give him to subscribe
    if user is None:
        await dialog_manager.start(StartSG.start,
                                   data={'user_id': user_id,
                                         'payload': payload})
    else:
        await dialog_manager.start(MainSG.main)

