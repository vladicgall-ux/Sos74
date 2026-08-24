from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import OWNER_ID
import db
from states import CompleteOrder, RefuseOrder
from keyboards import complete_order_kb, payment_method_kb, take_order_kb

router = Router()
router.message.filter(F.from_user.id != OWNER_ID)
router.callback_query.filter(F.from_user.id != OWNER_ID)


@router.message(Command("start"))
async def worker_start(message: Message):
    employees = dict(await db.get_employees())
    if message.from_user.id in employees:
        name = employees[message.from_user.id]
        await message.answer(
            f"👋 Здравствуйте, {name}!\n\n"
            "Вы подключены как сотрудник службы вскрытия замков SOS74.\n\n"
            "Как это работает:\n"
            "1️⃣ Когда поступает новая заявка — вам придёт адрес и описание проблемы с кнопкой «Взять в работу».\n"
            "2️⃣ Кто из сотрудников нажмёт первым — тот и берёт заявку себе, остальным придёт отметка, что заявка уже занята.\n"
            "3️⃣ После выполнения работы нажмите «Завершить и сдать отчёт» и заполните: стоимость, точную причину поломки, расход, способ оплаты и комментарий.\n\n"
            "Удачной работы! 🔧"
        )
    else:
        await message.answer(
            "👋 Здравствуйте! Это бот службы вскрытия замков SOS74.\n\n"
            f"Ваш Telegram ID: <code>{message.from_user.id}</code>\n\n"
            "Отправьте этот ID руководителю, чтобы он добавил вас в список сотрудников. "
            "После этого вы начнёте получать заявки прямо сюда."
        )


@router.callback_query(F.data.startswith("take_"))
async def take_order(call: CallbackQuery):
    order_id = int(call.data.split("_", 1)[1])
    employees = dict(await db.get_employees())
    if call.from_user.id not in employees:
        await call.answer("Вы не в списке сотрудников.", show_alert=True)
        return

    full_name = employees[call.from_user.id]
    ok = await db.take_order(order_id, call.from_user.id, full_name)
    if not ok:
        current = await db.get_order(order_id)
        if current and current["status"] == "cancelled":
            await call.answer("Заявка отменена администратором.", show_alert=True)
        else:
            await call.answer("Заявка уже взята другим сотрудником.", show_alert=True)
        return

    order = await db.get_order(order_id)
    await call.message.edit_text(
        f"🔧 Заявка №{order_id} — в работе\n"
        f"📍 {order['address']}\n"
        f"{order['problem']}\n\n"
        f"Исполнитель: {full_name}",
        reply_markup=complete_order_kb(order_id),
    )
    await call.answer("Заявка ваша ✅")
    await call.bot.send_message(
        OWNER_ID,
        f"👷 {full_name} взял в работу заявку №{order_id} ({order['address']})",
    )


@router.callback_query(F.data.startswith("cancel_"))
async def cancel_order(call: CallbackQuery):
    order_id = int(call.data.split("_", 1)[1])
    order = await db.get_order(order_id)
    if not order or order["assigned_to"] != call.from_user.id:
        await call.answer("Это не ваша заявка.", show_alert=True)
        return

    ok = await db.cancel_order(order_id, call.from_user.id)
    if not ok:
        await call.answer("Не удалось отменить заявку.", show_alert=True)
        return

    await call.message.edit_text(
        f"❌ Вы отменили заявку №{order_id}\n"
        f"📍 {order['address']}\n"
        f"{order['problem']}"
    )
    await call.answer("Заявка отменена")

    await call.bot.send_message(
        OWNER_ID,
        f"⚠️ {order['assigned_name']} отменил(а) заявку №{order_id} ({order['address']}).\n"
        "Заявка снова отправлена сотрудникам.",
    )

    employees = await db.get_employees()
    text = (
        f"🆕 Заявка №{order_id} (повторно)\n\n"
        f"📍 Адрес: {order['address']}\n"
        f"🔧 Проблема: {order['problem']}"
    )
    for user_id, _ in employees:
        try:
            await call.bot.send_message(user_id, text, reply_markup=take_order_kb(order_id))
        except Exception:
            pass


@router.callback_query(F.data.startswith("refuse_"))
async def refuse_order_start(call: CallbackQuery, state: FSMContext):
    order_id = int(call.data.split("_", 1)[1])
    order = await db.get_order(order_id)
    if not order or order["assigned_to"] != call.from_user.id:
        await call.answer("Это не ваша заявка.", show_alert=True)
        return
    await state.update_data(order_id=order_id)
    await state.set_state(RefuseOrder.reason)
    await call.message.answer(
        'Укажите причину отказа клиента (или отправьте "-" чтобы пропустить):'
    )
    await call.answer()


@router.message(RefuseOrder.reason)
async def refuse_order_reason(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data["order_id"]
    reason = "" if message.text.strip() == "-" else message.text
    await state.clear()

    ok = await db.refuse_order(order_id, message.from_user.id, reason)
    if not ok:
        await message.answer("Не удалось оформить отказ — заявка уже недоступна.")
        return

    order = await db.get_order(order_id)
    await message.answer(f"🚫 Заявка №{order_id} закрыта как отказ клиента.")

    await message.bot.send_message(
        OWNER_ID,
        f"🚫 Клиент отказался — заявка №{order_id}\n"
        f"📍 Адрес: {order['address']}\n"
        f"👷 Исполнитель: {order['assigned_name']}\n"
        f"💬 Причина: {reason or '—'}",
    )


@router.callback_query(F.data.startswith("complete_"))
async def complete_order_start(call: CallbackQuery, state: FSMContext):
    order_id = int(call.data.split("_", 1)[1])
    order = await db.get_order(order_id)
    if not order or order["assigned_to"] != call.from_user.id or order["status"] != "in_progress":
        await call.answer("Это не ваша заявка.", show_alert=True)
        return
    await state.update_data(order_id=order_id)
    await state.set_state(CompleteOrder.cost)
    await call.message.answer("📝 Отчёт по заявке\n\n1/5. Введите стоимость работы для клиента (₽):")
    await call.answer()


@router.message(CompleteOrder.cost)
async def complete_order_cost(message: Message, state: FSMContext):
    try:
        cost = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Введите число, например 1500")
        return
    await state.update_data(cost=cost)
    await state.set_state(CompleteOrder.diagnosis)
    await message.answer("2/5. Укажите точную причину поломки (что было с замком по факту):")


@router.message(CompleteOrder.diagnosis)
async def complete_order_diagnosis(message: Message, state: FSMContext):
    await state.update_data(diagnosis=message.text)
    await state.set_state(CompleteOrder.expenses)
    await message.answer("3/5. Введите расход (материалы, инструменты и т.п.), ₽:")


@router.message(CompleteOrder.expenses)
async def complete_order_expenses(message: Message, state: FSMContext):
    try:
        expenses = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Введите число, например 300")
        return
    await state.update_data(expenses=expenses)
    await state.set_state(CompleteOrder.payment_method)
    await message.answer("4/5. Способ оплаты:", reply_markup=payment_method_kb())


@router.callback_query(CompleteOrder.payment_method, F.data.startswith("pay_"))
async def complete_order_payment(call: CallbackQuery, state: FSMContext):
    payment_method = "💵 Наличные" if call.data == "pay_cash" else "💳 Перевод (безнал)"
    await state.update_data(payment_method=payment_method)
    await state.set_state(CompleteOrder.comment)
    await call.message.edit_text(f"Способ оплаты: {payment_method}")
    await call.message.answer('5/5. Комментарий к заявке (или отправьте "-" чтобы пропустить):')
    await call.answer()


@router.message(CompleteOrder.comment)
async def complete_order_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data["order_id"]
    cost = data["cost"]
    diagnosis = data["diagnosis"]
    expenses = data["expenses"]
    payment_method = data["payment_method"]
    comment = "" if message.text.strip() == "-" else message.text

    total = await db.complete_order(order_id, cost, diagnosis, expenses, payment_method, comment)
    await state.clear()

    order = await db.get_order(order_id)
    await message.answer(f"✅ Заявка №{order_id} закрыта. Итог: {total}₽")

    await message.bot.send_message(
        OWNER_ID,
        f"✅ Заявка №{order_id} завершена\n"
        f"📍 Адрес: {order['address']}\n"
        f"👷 Исполнитель: {order['assigned_name']}\n"
        f"🔍 Причина поломки: {diagnosis}\n"
        f"💰 Стоимость: {cost}₽\n"
        f"💸 Расход: {expenses}₽\n"
        f"🏦 Оплата: {payment_method}\n"
        f"📈 Итог: {total}₽\n"
        f"💬 Комментарий: {comment or '—'}",
    )
