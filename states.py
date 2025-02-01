from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    height = State()
    weight = State()
    age = State()
    action_level = State()
    city = State()
    goal = State()
    food_grams = State()
