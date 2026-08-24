from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import OWNER_ID
import db
from states import NewOrder, AddWorker
from keyboards import take_order_kb, report_period_kb, active_orders_kb

router = Router()
router.message.filter(F.from_user.id == OWNER_ID)
router.callback_query.filter(F.from_user.id == OWNER_ID)


@router.message(Command("start"))
async def owner_start(message: Message):
    await message.answer(
        "Привет! Это бот заявок для вашей мастерской.\n\n"
        "/new — создать новую заявку\n"
        "/orders — активные заявки\n"
        "/report — отчёт по выполненным работам\n"
        "/workers — список сотрудников\n"
        "/add_worker — добавить сотрудника\n"
        "/del_worker &lt;ID&gt; — удалить сотрудника"
    )


@router.message(Command("new"))
async def new_order_start(message: Message, state: FSMContext):
    await state.set_state(NewOrder.address)
    await message.answer("Введите адрес объекта:")


@router.message(NewOrder.address)
async def new_order_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(NewOrder.problem)
    await message.answer("Опишите проблему (что случилось с замком):")


@router.message(NewOrder.problem)
async def new_order_problem(message: Message, state: FSMContext):
    data = await state.get_data()
    address = data["address"]
    problem = message.text
    order_id = await db.create_order(address, problem)
    await state.clear()

    await message.answer(f"✅ Заявка №{order_id} создана и отправлена сотрудникам.")

    employees = await db.get_employees()
    if not employees:
        await message.answer(
            "⚠️ У вас пока нет добавленных сотрудников — заявка сохранена, но никому не отправлена. "
            "Добавьте сотрудника через /add_worker"
        )
        return

    text = (
        f"🆕 Новая заявка №{order_id}\n\n"
        f"📍 Адрес: {address}\n"
        f"🔧 Проблема: {problem}"
    )
    for user_id, _ in employees:
        try:
            await message.bot.send_message(user_id, text, reply_markup=take_order_kb(order_id))
        except Exception:
            pass


@router.message(Command("orders"))
async def list_orders(message: Message):
    orders = await db.get_active_orders()
    if not orders:
        await message.answer("Активных заявок нет.")
        return
    lines = []
    for o in orders:
        status = "🆕 новая" if o["status"] == "new" else f"🔧 в работе ({o['assigned_name']})"
        lines.append(f"№{o['id']} — {o['address']} — {status}")
    await message.answer("\n".join(lines), reply_markup=active_orders_kb(orders))


@router.callback_query(F.data.startswith("admincancel_"))
async def admin_cancel_order(call: CallbackQuery):
    order_id = int(call.data.split("_", 1)[1])
    order = await db.get_order(order_id)
    if not order or order["status"] not in ("new", "in_progress"):
        await call.answer("Заявка уже не активна.", show_alert=True)
        return

    ok = await db.admin_cancel_order(order_id)
    if not ok:
        await call.answer("Не удалось отменить заявку.", show_alert=True)
        return

    await call.answer("Заявка отменена")
    await call.message.answer(f"❌ Заявка №{order_id} ({order['address']}) отменена вами.")

    if order["status"] == "in_progress" and order["assigned_to"]:
        try:
            await call.bot.send_message(
                order["assigned_to"],
                f"❌ Заявка №{order_id} ({order['address']}) отменена администратором.",
            )
        except Exception:
            pass
    else:
        employees = await db.get_employees()
        for user_id, _ in employees:
            try:
                await call.bot.send_message(
                    user_id,
                    f"❌ Заявка №{order_id} ({order['address']}) отменена администратором.",
                )
            except Exception:
                pass


@router.message(Command("report"))
async def report_start(message: Message):
    await message.answer("Выберите период отчёта:", reply_markup=report_period_kb())


@router.callback_query(F.data.startswith("report_"))
async def report_period(call: CallbackQuery):
    period = call.data.split("_", 1)[1]
    now = datetime.now()
    if period == "today":
        date_from = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        title = "за сегодня"
    elif period == "week":
        date_from = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        ).isoformat()
        title = "за эту неделю"
    else:
        date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        title = "за этот месяц"
    date_to = now.isoformat()

    orders = await db.get_orders_between(date_from, date_to)
    if not orders:
        await call.message.edit_text(f"Нет завершённых заявок {title}.")
        await call.answer()
        return

    total_cost = sum(o["cost"] or 0 for o in orders)
    total_expenses = sum(o["expenses"] or 0 for o in orders)
    total_profit = sum(o["total"] or 0 for o in orders)

    lines = [f"📊 Отчёт {title}\n"]
    for o in orders:
        lines.append(
            f"№{o['id']} {o['address']} — исполнитель: {o['assigned_name']}\n"
            f"  Причина: {o['diagnosis'] or '—'}\n"
            f"  Стоимость: {o['cost']}₽, расход: {o['expenses']}₽, итог: {o['total']}₽, "
            f"оплата: {o['payment_method'] or '—'}"
        )
    lines.append(f"\nВсего заявок: {len(orders)}")
    lines.append(f"Сумма по стоимости: {total_cost}₽")
    lines.append(f"Сумма расходов: {total_expenses}₽")
    lines.append(f"Чистая прибыль: {total_profit}₽")

    text = "\n".join(lines)
    # Telegram limits messages to 4096 chars
    if len(text) > 4000:
        text = text[:4000] + "\n\n...(отчёт обрезан, слишком много заявок)"

    await call.message.edit_text(text)
    await call.answer()


@router.message(Command("workers"))
async def list_workers(message: Message):
    employees = await db.get_employees()
    if not employees:
        await message.answer("Сотрудников пока нет. Добавьте через /add_worker")
        return
    lines = [f"{name} — ID: {uid}" for uid, name in employees]
    await message.answer("👷 Сотрудники:\n" + "\n".join(lines))


@router.message(Command("add_worker"))
async def add_worker_start(message: Message, state: FSMContext):
    await state.set_state(AddWorker.waiting_id)
    await message.answer(
        "Пришлите Telegram ID сотрудника.\n"
        "Сотрудник может узнать свой ID, написав этому боту /start."
    )


@router.message(AddWorker.waiting_id)
async def add_worker_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("ID должен быть числом. Попробуйте ещё раз:")
        return
    await state.update_data(user_id=int(message.text))
    await state.set_state(AddWorker.waiting_name)
    await message.answer("Как зовут сотрудника?")


@router.message(AddWorker.waiting_name)
async def add_worker_name(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_employee(data["user_id"], message.text)
    await state.clear()
    await message.answer(f"✅ Сотрудник {message.text} добавлен.")


@router.message(Command("del_worker"))
async def del_worker(message: Message):
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Использование: /del_worker <ID>")
        return
    await db.remove_employee(int(parts[1]))
    await message.answer("Сотрудник удалён.")
