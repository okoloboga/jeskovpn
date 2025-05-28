from aiogram.fsm.state import State, StatesGroup

class PaymentSG(StatesGroup):
    custom_balance = State()
    add_balance = State()
    buy_subscription = State()
    add_device = State()
    add_email = State()

class DevicesSG(StatesGroup):
    device_name = State()
    rename_device = State()
    select_instruction = State()
    enter_promo = State()
    device_promo = State()

class RaffleStates(StatesGroup):
    select_tickets = State()
    confirm_payment = State()

class SupportSG(StatesGroup):
    create_ticket = State()

class AdminAuthStates(StatesGroup):
    waiting_for_new_password = State()
    waiting_for_password = State()
    waiting_for_broadcast_message = State()
    waiting_for_broadcast_image = State()
    waiting_for_broadcast_confirmation = State()
    waiting_for_new_admin_id = State()
    add_balance = State()
    add_promo_code = State()
    add_promo_type = State()
    add_promo_max_usage = State()
    search_users = State()
    enter_json = State()
    enter_key_limit = State()

class RaffleAdminStates(StatesGroup):
    select_type = State()
    enter_name = State()
    enter_ticket_price = State()
    enter_start_date = State()
    enter_end_date = State()
    upload_images = State()
    edit_field = State()
    select_winner = State()
    add_tickets = State()
    select_raffle = State()
    select_user = State()
    waiting_for_raffle_confirmation = State()
