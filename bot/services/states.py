from aiogram.fsm.state import State, StatesGroup

class PaymentSG(StatesGroup):
    custom_balance = State()
    add_balance = State()
    buy_subscription = State()
    add_device = State()

class DevicesSG(StatesGroup):
    device_name = State()
    rename_device = State()

class SupportSG(StatesGroup):
    create_ticket = State()

class AdminAuthStates(StatesGroup):
    waiting_for_new_password = State()
    waiting_for_password = State()
