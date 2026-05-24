from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


# ─── Главное меню ─────────────────────────────────────────

def main_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(
        KeyboardButton(text="🛍 Каталог"),
        KeyboardButton(text="🛒 Корзина"),
    )
    kb.row(
        KeyboardButton(text="📦 Мои заказы"),
        KeyboardButton(text="ℹ️ О магазине"),
    )
    return kb.as_markup(resize_keyboard=True)


def admin_menu() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.row(
        KeyboardButton(text="🛍 Каталог"),
        KeyboardButton(text="🛒 Корзина"),
    )
    kb.row(
        KeyboardButton(text="📦 Мои заказы"),
        KeyboardButton(text="ℹ️ О магазине"),
    )
    kb.row(KeyboardButton(text="⚙️ Админ панель"))
    return kb.as_markup(resize_keyboard=True)


# ─── Каталог ──────────────────────────────────────────────

def categories_keyboard(categories: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=f"📂 {cat}", callback_data=f"cat:{cat}")
    builder.adjust(2)
    return builder.as_markup()


def products_keyboard(products: list[dict], category: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for p in products:
        builder.button(
            text=f"{p['name']} — {p['price']:,.0f} ₽",
            callback_data=f"product:{p['id']}"
        )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back:catalog"))
    return builder.as_markup()


def product_keyboard(product_id: int, category: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 В корзину", callback_data=f"addcart:{product_id}")
    builder.button(text="◀️ Назад", callback_data=f"cat:{category}")
    builder.adjust(1)
    return builder.as_markup()


# ─── Корзина ──────────────────────────────────────────────

def cart_keyboard(items: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.button(
            text=f"❌ {item['name']}",
            callback_data=f"removecart:{item['id']}"
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout"),
        InlineKeyboardButton(text="🗑 Очистить", callback_data="clearcart"),
    )
    return builder.as_markup()


# ─── Оформление заказа ────────────────────────────────────

def cancel_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.add(KeyboardButton(text="❌ Отмена"))
    return kb.as_markup(resize_keyboard=True)


def confirm_order_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data="confirm_order")
    builder.button(text="✏️ Изменить", callback_data="edit_order")
    builder.adjust(2)
    return builder.as_markup()


# ─── Заказы ───────────────────────────────────────────────

STATUS_LABELS = {
    "new": "🆕 Новый",
    "processing": "⚙️ В работе",
    "shipped": "🚚 Отправлен",
    "delivered": "✅ Доставлен",
    "cancelled": "❌ Отменён",
}


def order_status_keyboard(order_id: int) -> InlineKeyboardMarkup:
    statuses = ["processing", "shipped", "delivered", "cancelled"]
    builder = InlineKeyboardBuilder()
    for s in statuses:
        builder.button(text=STATUS_LABELS[s], callback_data=f"setstatus:{order_id}:{s}")
    builder.adjust(2)
    return builder.as_markup()


# ─── Админ панель ─────────────────────────────────────────

def admin_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Статистика", callback_data="admin:stats")
    builder.button(text="📋 Новые заказы", callback_data="admin:new_orders")
    builder.button(text="➕ Добавить товар", callback_data="admin:add_product")
    builder.button(text="📦 Все товары", callback_data="admin:all_products")
    builder.adjust(2)
    return builder.as_markup()


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
