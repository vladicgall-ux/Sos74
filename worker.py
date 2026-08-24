from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import OWNER_ID
import db
from states import CompleteOrder, RefuseOrder
from keyboards import complete_order_kb, payment_method_kb, take_order_kb, period_kb, worker_menu_kb
from utils import period_range, format_order_date

router = Router()
router.message.filter(F.from_user.id != OWNER_ID)
router.callback_query.filter(F.from_user.id != OWNER_ID)

LESSONS = {
    "🔑 Цилиндровые замки": (
        "🔑 Урок: аварийное вскрытие цилиндровых замков\n\n"
        "https://www.youtube.com/watch?v=hiBRi2DfjmA"
    ),
    "🔐 Сувальдные замки": (
        "🔐 Урок: аварийное вскрытие сувальдных замков\n\n"
        "https://www.youtube.com/watch?v=dY1YyaUtnlg"
    ),
    "🗄️ Сейфы": (
        "🗄️ Урок: аварийное вскрытие сейфов\n\n"
        "https://www.youtube.com/watch?v=05sxJh9E5Ew"
    ),
    "🚪 Гаражные замки": (
        "🚪 Урок: аварийное вскрытие гаражных (навесных) замков\n\n"
        "https://www.youtube.com/watch?v=o2PCPRtpjrk"
    ),
}


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
            "3️⃣ После выполнения работы нажмите «Завершить и сдать отчёт» и заполните: стоимость, точную причину поломки, расход, способ оплаты и комментарий.\n"
            "4️⃣ Команда /report или кнопка «📊 Мои отчёты» — посмотреть свои завершённые заявки за период.\n"
            "5️⃣ Кнопки с замками внизу — обучающие видео по аварийному вскрытию.\n\n"
            "Удачной работы! 🔧",
            reply_markup=worker_menu_kb(),
        )
    else:
        await message.answer(
            "👋 Здравствуйте! Это бот службы вскрытия замков SOS74.\n\n"
            f"Ваш Telegram ID: <code>{message.from_user.id}</code>\n\n"
            "Отправьте этот ID руководителю, чтобы он добавил вас в список сотрудников. "
            "После этого вы начнёте получать заявки прямо сюда."
        )


@router.message(Command("report"))
@router.message(F.text == "📊 Мои отчёты")
async def worker_report_start(message: Message):
    await message.answer("Выберите период отчёта:", reply_markup=period_kb("wreport"))


@router.message(F.text.in_(LESSONS.keys()))
async def worker_lesson(message: Message):
    await message.answer(LESSONS[message.text])


@router.callback_query(F.data.startswith("wreport_"))
async def worker_report_period(call: CallbackQuery):
    period = call.data.split("_", 1)[1]
    date_from, date_to, title = period_range(period)

    orders = await db.get_orders_between(date_from, date_to, call.from_user.id)
    if not orders:
        await call.message.edit_text(f"У вас нет завершённых заявок {title}.")
        await call.answer()
        return

    total_cost = sum(o["cost"] or 0 for o in orders)
    total_expenses = sum(o["expenses"] or 0 for o in orders)
    total_profit = sum(o["total"] or 0 for o in orders)

    lines = [f"📊 Ваш отчёт {title}\n"]
    for o in orders:
        lines.append(
            f"№{o['id']} {o['address']} ({format_order_date(o['completed_at'])})\n"
            f"  Причина: {o['diagnosis'] or '—'}\n"
            f"  Стоимость: {o['cost']}₽, расход: {o['expenses']}₽, итог: {o['total']}₽, "
            f"оплата: {o['payment_method'] or '—'}"
        )
    lines.append(f"\nВсего заявок: {len(orders)}")
    lines.append(f"Сумма по стоимости: {total_cost}₽")
    lines.append(f"Сумма расходов: {total_expenses}₽")
    lines.append(f"Чистая прибыль: {total_profit}₽")

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n\n...(отчёт обрезан, слишком много заявок)"

    await call.message.edit_text(text)
    await call.answer()


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
    await call.message.answer("📝 Отчёт по заявке\n\n1/3. Введите стоимость работы для клиента (₽):")
    await call.answer()


@router.message(CompleteOrder.cost)
async def complete_order_cost(message: Message, state: FSMContext):
    try:
        cost = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Введите число, например 1500")
        return
    await state.update_data(cost=cost)
    await state.set_state(CompleteOrder.expenses)
    await message.answer("2/3. Введите расход материала (₽):")


@router.message(CompleteOrder.expenses)
async def complete_order_expenses(message: Message, state: FSMContext):
    try:
        expenses = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Введите число, например 300")
        return
    await state.update_data(expenses=expenses)
    await state.set_state(CompleteOrder.payment_method)
    await message.answer("3/3. Способ оплаты:", reply_markup=payment_method_kb())


@router.callback_query(CompleteOrder.payment_method, F.data.startswith("pay_"))
async def complete_order_payment(call: CallbackQuery, state: FSMContext):
    payment_method = "💵 Наличные" if call.data == "pay_cash" else "💳 Перевод (безнал)"
    data = await state.get_data()
    order_id = data["order_id"]
    cost = data["cost"]
    expenses = data["expenses"]

    total = await db.complete_order(order_id, cost, "", expenses, payment_method, "")
    await state.clear()

    order = await db.get_order(order_id)
    await call.message.edit_text(f"Способ оплаты: {payment_method}")
    await call.message.answer(f"✅ Заявка №{order_id} закрыта. Итог: {total}₽")
    await call.answer()

    await call.bot.send_message(
        OWNER_ID,
        f"✅ Заявка №{order_id} завершена\n"
        f"📍 Адрес: {order['address']}\n"
        f"👷 Исполнитель: {order['assigned_name']}\n"
        f"💰 Стоимость: {cost}₽\n"
        f"💸 Расход: {expenses}₽\n"
        f"🏦 Оплата: {payment_method}\n"
        f"📈 Итог: {total}₽",
    )
