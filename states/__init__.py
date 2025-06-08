from aiogram.fsm.state import State, StatesGroup

class WeatherStates(StatesGroup):
    waiting_for_city = State()

class FavoriteStates(StatesGroup):
    waiting_for_add_city = State()
    waiting_for_remove_city = State()

class AdminStates(StatesGroup):
    waiting_for_broadcast_message = State()
    waiting_for_ban_user_id = State()
    waiting_for_unban_user_id = State()
    waiting_for_ban_reason = State()