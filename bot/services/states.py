from aiogram.fsm.state import State, StatesGroup

class PaymentSG(StatesGroup):
    custom_balance = State()

class SupportSG(StatesGroup):
    create_ticket = State()

class AdminSG(StatesGroup):
    reply_ticket = State()