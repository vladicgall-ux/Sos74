import aiosqlite
from datetime import datetime

from config import DB_PATH


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            added_at TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT,
            problem TEXT,
            status TEXT DEFAULT 'new',
            created_at TEXT,
            assigned_to INTEGER,
            assigned_name TEXT,
            taken_at TEXT,
            cost REAL,
            expenses REAL,
            total REAL,
            comment TEXT,
            completed_at TEXT,
            diagnosis TEXT,
            payment_method TEXT
        )""")
        await db.commit()

        # Migration for databases created before diagnosis/payment_method existed
        cursor = await db.execute("PRAGMA table_info(orders)")
        columns = [row[1] for row in await cursor.fetchall()]
        if "diagnosis" not in columns:
            await db.execute("ALTER TABLE orders ADD COLUMN diagnosis TEXT")
        if "payment_method" not in columns:
            await db.execute("ALTER TABLE orders ADD COLUMN payment_method TEXT")
        await db.commit()


async def add_employee(user_id: int, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO employees (user_id, full_name, added_at) VALUES (?, ?, ?)",
            (user_id, full_name, datetime.now().isoformat()),
        )
        await db.commit()


async def remove_employee(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM employees WHERE user_id = ?", (user_id,))
        await db.commit()


async def get_employees():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT user_id, full_name FROM employees")
        return await cursor.fetchall()


async def create_order(address: str, problem: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO orders (address, problem, status, created_at) VALUES (?, ?, 'new', ?)",
            (address, problem, datetime.now().isoformat()),
        )
        await db.commit()
        return cursor.lastrowid


async def get_order(order_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        return await cursor.fetchone()


async def take_order(order_id: int, user_id: int, full_name: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
        row = await cursor.fetchone()
        if not row or row[0] != "new":
            return False
        await db.execute(
            "UPDATE orders SET status='in_progress', assigned_to=?, assigned_name=?, taken_at=? WHERE id=?",
            (user_id, full_name, datetime.now().isoformat(), order_id),
        )
        await db.commit()
        return True


async def cancel_order(order_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT status, assigned_to FROM orders WHERE id = ?", (order_id,)
        )
        row = await cursor.fetchone()
        if not row or row[0] != "in_progress" or row[1] != user_id:
            return False
        await db.execute(
            """UPDATE orders
               SET status='new', assigned_to=NULL, assigned_name=NULL, taken_at=NULL
               WHERE id=?""",
            (order_id,),
        )
        await db.commit()
        return True


async def refuse_order(order_id: int, user_id: int, reason: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT status, assigned_to FROM orders WHERE id = ?", (order_id,)
        )
        row = await cursor.fetchone()
        if not row or row[0] != "in_progress" or row[1] != user_id:
            return False
        await db.execute(
            """UPDATE orders
               SET status='refused', comment=?, completed_at=?
               WHERE id=?""",
            (reason, datetime.now().isoformat(), order_id),
        )
        await db.commit()
        return True


async def admin_cancel_order(order_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT status FROM orders WHERE id = ?", (order_id,))
        row = await cursor.fetchone()
        if not row or row[0] not in ("new", "in_progress"):
            return False
        await db.execute(
            "UPDATE orders SET status='cancelled', completed_at=? WHERE id=?",
            (datetime.now().isoformat(), order_id),
        )
        await db.commit()
        return True


async def complete_order(
    order_id: int,
    cost: float,
    diagnosis: str,
    expenses: float,
    payment_method: str,
    comment: str,
) -> float:
    total = cost - expenses
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE orders
               SET status='done', cost=?, diagnosis=?, expenses=?, payment_method=?,
                   total=?, comment=?, completed_at=?
               WHERE id=?""",
            (cost, diagnosis, expenses, payment_method, total, comment,
             datetime.now().isoformat(), order_id),
        )
        await db.commit()
    return total


async def get_active_orders():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM orders WHERE status NOT IN ('done', 'refused', 'cancelled') ORDER BY id DESC"
        )
        return await cursor.fetchall()


async def get_orders_between(date_from: str, date_to: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM orders WHERE status='done' AND completed_at BETWEEN ? AND ? ORDER BY completed_at",
            (date_from, date_to),
        )
        return await cursor.fetchall()
