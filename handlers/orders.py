from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS
from database import get_cart, clear_cart, create_order, get_orders
from keyboards.kb import (
    cancel_keyboard, confirm_order_keyboard, main_menu, admin_menu, remove_keyboard
)

router = Router()


class OrderForm(StatesGroup):
    name = State()
    phone = State()
    address = State()
    confirm = State()


STATUS_EMOJI = {
    "new": "🆕",
    "processing": "⚙️",
    "shipped": "🚚",
    "delivered": "✅",
    "cancelled": "❌",
}


@router.callback_query(F.data == "checkout")
async def checkout_start(call: CallbackQuery, state: FSMContext):
    items = await get_cart(call.from_user.id)
    if not items:
        await call.answer("Корзина пуста!", show_alert=True)
        return

    total = sum(i["price"] * i["quantity"] for i in items)
    await state.update_data(items=items, total=total)
    await state.set_state(OrderForm.name)

    await call.message.answer(
        "📝 <b>Оформление заказа</b>\n\n"
        "Введите ваше <b>имя и фамилию</b>:",
        reply_markup=cancel_keyboard()
    )
    await call.answer()


@router.message(OrderForm.name, F.text == "❌ Отмена")
@router.message(OrderForm.phone, F.text == "❌ Отмена")
@router.message(OrderForm.address, F.text == "❌ Отмена")
async def cancel_order(message: Message, state: FSMContext):
    await state.clear()
    is_admin = message.from_user.id in ADMIN_IDS
    kb = admin_menu() if is_admin else main_menu()
    await message.answer("❌ Оформление отменено", reply_markup=kb)


@router.message(OrderForm.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(OrderForm.phone)
    await message.answer("📱 Введите ваш <b>номер телефона</b>:")


@router.message(OrderForm.phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(OrderForm.address)
    await message.answer("🏠 Введите <b>адрес доставки</b>:")


@router.message(OrderForm.address)
async def get_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()
    await state.set_state(OrderForm.confirm)

    items_text = "\n".join(
        f"• {i['name']} × {i['quantity']} = {i['price'] * i['quantity']:,.0f} ₽"
        for i in data["items"]
    )

    await message.answer(
        f"📋 <b>Проверьте данные заказа:</b>\n\n"
        f"👤 Имя: {data['name']}\n"
        f"📱 Телефон: {data['phone']}\n"
        f"🏠 Адрес: {data['address']}\n\n"
        f"🛍 Товары:\n{items_text}\n\n"
        f"💰 <b>Итого: {data['total']:,.0f} ₽</b>",
        reply_markup=confirm_order_keyboard()
    )


@router.callback_query(OrderForm.confirm, F.data == "edit_order")
async def edit_order(call: CallbackQuery, state: FSMContext):
    await state.set_state(OrderForm.name)
    await call.message.answer("✏️ Введите имя заново:")
    await call.answer()


@router.callback_query(OrderForm.confirm, F.data == "confirm_order")
async def confirm_order(call: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    await state.clear()

    items_str = "; ".join(
        f"{i['name']} x{i['quantity']}" for i in data["items"]
    )

    order_id = await create_order(
        user_id=call.from_user.id,
        items=items_str,
        total=data["total"],
        name=data["name"],
        phone=data["phone"],
        address=data["address"]
    )

    await clear_cart(call.from_user.id)

    is_admin = call.from_user.id in ADMIN_IDS
    kb = admin_menu() if is_admin else main_menu()

    await call.message.answer(
        f"🎉 <b>Заказ #{order_id} оформлен!</b>\n\n"
        f"Ожидайте звонка для подтверждения.\n"
        f"Статус заказа можно отследить в разделе <b>«Мои заказы»</b>.",
        reply_markup=kb
    )
    await call.answer()

    # Уведомляем администраторов
    user = call.from_user
    admin_text = (
        f"🆕 <b>Новый заказ #{order_id}!</b>\n\n"
        f"👤 {data['name']}\n"
        f"📱 {data['phone']}\n"
        f"🏠 {data['address']}\n"
        f"🛍 {items_str}\n"
        f"💰 {data['total']:,.0f} ₽\n\n"
        f"TG: @{user.username or 'нет'} (ID: {user.id})"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text)
        except Exception:
            pass


@router.message(F.text == "📦 Мои заказы")
async def my_orders(message: Message):
    orders = await get_orders(message.from_user.id)
    if not orders:
        await message.answer("У вас пока нет заказов.")
        return

    lines = ["📦 <b>Ваши заказы:</b>\n"]
    for o in orders:
        emoji = STATUS_EMOJI.get(o["status"], "❓")
        lines.append(
            f"<b>Заказ #{o['id']}</b> {emoji} {o['status']}\n"
            f"   🛍 {o['items']}\n"
            f"   💰 {o['total']:,.0f} ₽\n"
            f"   📅 {o['created_at'][:16]}\n"
        )
    await message.answer("\n".join(lines))
