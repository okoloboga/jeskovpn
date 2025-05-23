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

class SupportSG(StatesGroup):
    create_ticket = State()

class AdminAuthStates(StatesGroup):
    waiting_for_new_password = State()
    waiting_for_password = State()
    waiting_for_broadcast_message = State()
    waiting_for_new_admin_id = State()
    add_balance = State()
    add_promo_code = State()
    add_promo_type = State()
    add_promo_max_usage = State()
    search_users = State()
    enter_json = State()
