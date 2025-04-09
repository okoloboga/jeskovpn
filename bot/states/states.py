from aiogram.fsm.state import State, StatesGroup

class StartSG(StatesGroup):
    start = State()
    welcome = State()
    

class MainSG(StatesGroup):
    main = State()