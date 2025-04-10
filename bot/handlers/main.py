import logging

from aiogram import Router, F
from aiogram.utils.deep_linking import decode_payload
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import CallbackQuery, Message
from fluentogram import TranslatorRunner

from services import user_req
from keyboards import main_kb

main_router = Router()

logger = logging.getLogger(__name__)

# IS CORRECT FOR ALL DEVICES??
DEVICE_PRICE = "?????" 

logging.basicConfig(
    level=logging.INFO,
    format='%(filename)s:%(lineno)d #%(levelname)-8s '
           '[%(asctime)s] - %(name)s - %(message)s')

# Process START CommandStart
@main_router.message(CommandStart(deep_link_encoded=True))
async def command_start_getter(message: Message,
                               i18n: TranslatorRunner,
                               command: CommandObject):
    
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    username = message.from_user.username

    logger.info(f'Referral data: {command}')

    # If user start bot by referral link 
    if command.args:
        logger.info(f'CommandObject is {command}')
        args = command.args
        payload = decode_payload(args)
    else:
        payload = None

    user = await user_req.get_user(user_id)
    logger.info(f'User from database {user}')

    # Check for referral link
    if user in None:

        is_invited = False
        await user_req.create_user(user_id,
                                   first_name,
                                   last_name,
                                   username)
        
        logger.info(f'Payload before adding referral: {payload}')

        # Add referral to link Parent
        if payload is not None:
            await user_req.add_referral(payload, user_id)
            is_invited = True

    # ??? Add to Backend users model !!!
    is_subscripted = user.is_subscribed
    subscription_expires = user.subscription_expires
    user_language = user.language 
    balance = user.balance

    await message.answer(text=(i18n.start.invited if is_invited else i18n.start.default), 
                         reply_markup=main_kb.main_kb(i18n, 
                                                      is_subscripted, 
                                                      subscription_expires, 
                                                      balance, 
                                                      user_language)
                                                      )
    
@main_router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery,
                            i18n: TranslatorRunner):
    
    user_id = callback.from_user.id
    user = await user_req.get_user(user_id)

    # ??? Add to Backend users model !!!
    is_subscripted = user.is_subscribed
    subscription_expires = user.subscription_expires
    user_language = user.language 
    balance = user.balance

    await callback.message.answer(text=i18n.start.default,
                                  reply_markup=main_kb.main_kb(i18n, 
                                                               is_subscripted, 
                                                               subscription_expires, 
                                                               balance, 
                                                               user_language)
                                                               )
    

@main_router.message((F.text == "") | (F.text == "")) # FILL CORRECT MESSAGES!
@main_router.callback_query(F.data == 'devices_menu')
async def devices_menu(message: Message,
                       i18n: TranslatorRunner):
    
    user_id = message.from_user.id

    # ??? Add to Backend users model IN GET_USER !!!
    user = await user_req.get_user(user_id)
    devices = user.devices
    combo_cells = user.combo_cells
    subscription_fee = devices * DEVICE_PRICE # NEED TO KNOW

    await message.answer(text=i18n.devices.menu(subscription_fee=subscription_fee),
                         reply_markup=main_kb.devices_kb(i18n, devices, combo_cells))


@main_router.callback_query(F.data.startswith("selected_device_"))
async def select_device(callback: CallbackQuery,
                        i18n: TranslatorRunner):
    
    user_id = callback.from_user.id
    _, _, device = callback.data.split('_')
    device_key = await user_req.get_device_key(user_id, device)

    await callback.message.edit_text(text=i18n.device.menu(device=device, device_key=device_key),
                                     reply_markup=main_kb.device_kb(i18n, device))


        