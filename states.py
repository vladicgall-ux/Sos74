from aiogram.fsm.state import StatesGroup, State


class NewOrder(StatesGroup):
    address = State()
    problem = State()


class CompleteOrder(StatesGroup):
    cost = State()
    diagnosis = State()
    expenses = State()
    payment_method = State()
    comment = State()


class AddWorker(StatesGroup):
    waiting_id = State()
    waiting_name = State()


class RefuseOrder(StatesGroup):
    reason = State()
