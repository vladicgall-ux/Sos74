from aiogram.fsm.state import StatesGroup, State


class NewOrder(StatesGroup):
    address = State()
    problem = State()


class CompleteOrder(StatesGroup):
    cost = State()
    expenses = State()
    payment_method = State()


class AddWorker(StatesGroup):
    waiting_id = State()
    waiting_name = State()


class RefuseOrder(StatesGroup):
    reason = State()
