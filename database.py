import aiosqlite
from typing import Optional

DB_PATH = "shop.db"


async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT NOT NULL,
                description TEXT,
                price       REAL NOT NULL,
                category    TEXT NOT NULL,
                photo_id    TEXT,
                in_stock    INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS users (
                id         INTEGER PRIMARY KEY,
                username   TEXT,
                full_name  TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS cart (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity   INTEGER DEFAULT 1,
                UNIQUE(user_id, product_id)
            );

            CREATE TABLE IF NOT EXISTS orders (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                items      TEXT NOT NULL,
                total      REAL NOT NULL,
                name       TEXT NOT NULL,
                phone      TEXT NOT NULL,
                address    TEXT NOT NULL,
                status     TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await db.commit()

        # Наполнение тестовыми товарами если база пустая
        cursor = await db.execute("SELECT COUNT(*) FROM products")
        count = (await cursor.fetchone())[0]
        if count == 0:
            await db.executemany(
                "INSERT INTO products (name, description, price, category) VALUES (?, ?, ?, ?)",
                [
                    ("Футболка Classic", "Хлопок 100%, размеры S-XL", 1490, "Одежда"),
                    ("Футболка Premium", "Органический хлопок, лимитированная серия", 2490, "Одежда"),
                    ("Худи Oversize", "Тёплое, с карманом кенгуру", 3990, "Одежда"),
                    ("Кепка Logo", "Регулируемый ремешок, 5 цветов", 990, "Аксессуары"),
                    ("Сумка Tote", "Плотный холст, объём 15л", 1290, "Аксессуары"),
                    ("Носки 3 пары", "Хлопок с рисунком", 590, "Аксессуары"),
                ]
            )
            await db.commit()


# ─── Товары ───────────────────────────────────────────────

async def get_categories() -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT DISTINCT category FROM products WHERE in_stock = 1 ORDER BY category"
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]


async def get_products(category: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM products WHERE category = ? AND in_stock = 1", (category,)
        )
        return [dict(r) for r in await cursor.fetchall()]


async def get_product(product_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def add_product(name: str, description: str, price: float, category: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO products (name, description, price, category) VALUES (?, ?, ?, ?)",
            (name, description, price, category)
        )
        await db.commit()
        return cursor.lastrowid


async def toggle_product_stock(product_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE products SET in_stock = 1 - in_stock WHERE id = ?", (product_id,)
        )
        await db.commit()


# ─── Пользователи ─────────────────────────────────────────

async def upsert_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO users (id, username, full_name) VALUES (?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET username=excluded.username, full_name=excluded.full_name""",
            (user_id, username, full_name)
        )
        await db.commit()


# ─── Корзина ──────────────────────────────────────────────

async def add_to_cart(user_id: int, product_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO cart (user_id, product_id, quantity) VALUES (?, ?, 1)
               ON CONFLICT(user_id, product_id) DO UPDATE SET quantity = quantity + 1""",
            (user_id, product_id)
        )
        await db.commit()


async def get_cart(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT p.id, p.name, p.price, c.quantity
               FROM cart c JOIN products p ON c.product_id = p.id
               WHERE c.user_id = ?""",
            (user_id,)
        )
        return [dict(r) for r in await cursor.fetchall()]


async def remove_from_cart(user_id: int, product_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id)
        )
        await db.commit()


async def clear_cart(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        await db.commit()


# ─── Заказы ───────────────────────────────────────────────

async def create_order(user_id: int, items: str, total: float,
                        name: str, phone: str, address: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO orders (user_id, items, total, name, phone, address) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, items, total, name, phone, address)
        )
        await db.commit()
        return cursor.lastrowid


async def get_orders(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 10",
            (user_id,)
        )
        return [dict(r) for r in await cursor.fetchall()]


async def get_all_orders(status: str = None) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if status:
            cursor = await db.execute(
                "SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC", (status,)
            )
        else:
            cursor = await db.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT 50")
        return [dict(r) for r in await cursor.fetchall()]


async def update_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        users = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        orders = (await (await db.execute("SELECT COUNT(*) FROM orders")).fetchone())[0]
        revenue = (await (await db.execute("SELECT COALESCE(SUM(total), 0) FROM orders WHERE status != 'cancelled'")).fetchone())[0]
        new_orders = (await (await db.execute("SELECT COUNT(*) FROM orders WHERE status = 'new'")).fetchone())[0]
        return {"users": users, "orders": orders, "revenue": revenue, "new_orders": new_orders}
