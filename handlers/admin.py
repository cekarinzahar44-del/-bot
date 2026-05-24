from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS
from database import (
    get_stats, get_all_orders, update_order_status,
    add_product, get_products, get_categories, toggle_product_stock
)
from keyboards.kb import admin_keyboard, order_status_keyboard, cancel_keyboard, main_menu, admin_menu

router = Router()


class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in ADMIN_IDS


class AddProductForm(StatesGroup):
    name = State()
    description = State()
    price = State()
    category = State()


# Применяем фильтр ко всему роутеру
router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())


@router.message(F.text == "⚙️ Админ панель")
async def admin_panel(message: Message):
    await message.answer("⚙️ <b>Панель администратора</b>", reply_markup=admin_keyboard())


@router.callback_query(F.data == "admin:stats")
async def show_stats(call: CallbackQuery):
    stats = await get_stats()
    await call.message.edit_text(
        f"📊 <b>Статистика магазина</b>\n\n"
        f"👥 Пользователей: <b>{stats['users']}</b>\n"
        f"📦 Заказов всего: <b>{stats['orders']}</b>\n"
        f"🆕 Новых заказов: <b>{stats['new_orders']}</b>\n"
        f"💰 Выручка: <b>{stats['revenue']:,.0f} ₽</b>",
        reply_markup=admin_keyboard()
    )


@router.callback_query(F.data == "admin:new_orders")
async def show_new_orders(call: CallbackQuery):
    orders = await get_all_orders(status="new")
    if not orders:
        await call.answer("Новых заказов нет", show_alert=True)
        return

    for o in orders[:5]:  # показываем первые 5
        await call.message.answer(
            f"🆕 <b>Заказ #{o['id']}</b>\n\n"
            f"👤 {o['name']}\n"
            f"📱 {o['phone']}\n"
            f"🏠 {o['address']}\n"
            f"🛍 {o['items']}\n"
            f"💰 {o['total']:,.0f} ₽\n"
            f"📅 {o['created_at'][:16]}",
            reply_markup=order_status_keyboard(o["id"])
        )
    await call.answer()


@router.callback_query(F.data.startswith("setstatus:"))
async def set_order_status(call: CallbackQuery):
    _, order_id, status = call.data.split(":")
    await update_order_status(int(order_id), status)
    await call.answer(f"Статус обновлён: {status}", show_alert=True)
    await call.message.edit_reply_markup(reply_markup=None)


# ─── Добавление товара ────────────────────────────────────

@router.callback_query(F.data == "admin:add_product")
async def add_product_start(call: CallbackQuery, state: FSMContext):
    await state.set_state(AddProductForm.name)
    await call.message.answer("📝 Введите <b>название товара</b>:", reply_markup=cancel_keyboard())
    await call.answer()


@router.message(AddProductForm.name, F.text == "❌ Отмена")
@router.message(AddProductForm.description, F.text == "❌ Отмена")
@router.message(AddProductForm.price, F.text == "❌ Отмена")
@router.message(AddProductForm.category, F.text == "❌ Отмена")
async def cancel_add(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено", reply_markup=admin_menu())


@router.message(AddProductForm.name)
async def get_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProductForm.description)
    await message.answer("📄 Введите <b>описание</b> (или «-» чтобы пропустить):")


@router.message(AddProductForm.description)
async def get_product_description(message: Message, state: FSMContext):
    desc = "" if message.text == "-" else message.text
    await state.update_data(description=desc)
    await state.set_state(AddProductForm.price)
    await message.answer("💰 Введите <b>цену</b> (число):")


@router.message(AddProductForm.price)
async def get_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("❌ Введите число, например: 1490")
        return
    await state.update_data(price=price)
    await state.set_state(AddProductForm.category)
    await message.answer("📂 Введите <b>категорию</b> (например: Одежда):")


@router.message(AddProductForm.category)
async def get_product_category(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.clear()

    product_id = await add_product(
        name=data["name"],
        description=data["description"],
        price=data["price"],
        category=message.text.strip()
    )

    await message.answer(
        f"✅ Товар добавлен (ID: {product_id})\n\n"
        f"<b>{data['name']}</b>\n"
        f"Цена: {data['price']:,.0f} ₽\n"
        f"Категория: {message.text}",
        reply_markup=admin_menu()
    )


# ─── Список товаров ───────────────────────────────────────

@router.callback_query(F.data == "admin:all_products")
async def all_products(call: CallbackQuery):
    categories = await get_categories()
    lines = ["📦 <b>Все товары:</b>\n"]
    for cat in categories:
        products = await get_products(cat)
        lines.append(f"\n<b>{cat}:</b>")
        for p in products:
            stock = "✅" if p["in_stock"] else "❌"
            lines.append(f"  {stock} #{p['id']} {p['name']} — {p['price']:,.0f} ₽")
    await call.message.answer("\n".join(lines))
    await call.answer()
