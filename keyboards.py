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
    kb.adjust(1)
    return kb.as_markup()


def payment_method_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💵 Наличные", callback_data="pay_cash")
    kb.button(text="💳 Перевод (безнал)", callback_data="pay_transfer")
    kb.adjust(1)
    return kb.as_markup()


def report_period_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="Сегодня", callback_data="report_today")
    kb.button(text="Эта неделя", callback_data="report_week")
    kb.button(text="Этот месяц", callback_data="report_month")
    kb.adjust(1)
    return kb.as_markup()
