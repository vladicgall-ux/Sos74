from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def take_order_kb(order_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🔧 Взять в работу", callback_data=f"take_{order_id}")
    return kb.as_markup()


def complete_order_kb(order_id: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Завершить и сдать отчёт", callback_data=f"complete_{order_id}")
    kb.button(text="❌ Отменить заявку", callback_data=f"cancel_{order_id}")
    kb.button(text="🚫 Отказ клиента", callback_data=f"refuse_{order_id}")
    kb.adjust(1)
    return kb.as_markup()


def active_orders_kb(orders) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for o in orders:
        kb.button(text=f"❌ Отменить №{o['id']}", callback_data=f"admincancel_{o['id']}")
    kb.adjust(1)
    return kb.as_markup()


def payment_method_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💵 Наличные", callback_data="pay_cash")
    kb.button(text="💳 Перевод (безнал)", callback_data="pay_transfer")
    kb.adjust(1)
    return kb.as_markup()


def period_kb(prefix: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Сегодня", callback_data=f"{prefix}_today")
    kb.button(text="Эта неделя", callback_data=f"{prefix}_week")
    kb.button(text="Этот месяц", callback_data=f"{prefix}_month")
    kb.adjust(1)
    return kb.as_markup()


def report_employees_kb(employees) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="👥 Все сотрудники", callback_data="repemp_all")
    for user_id, name in employees:
        kb.button(text=name, callback_data=f"repemp_{user_id}")
    kb.adjust(1)
    return kb.as_markup()


def worker_menu_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="📊 Мои отчёты", callback_data="wreport_menu")
    return kb.as_markup()
