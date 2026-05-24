from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database import add_to_cart, get_cart, remove_from_cart, clear_cart
from keyboards.kb import cart_keyboard

router = Router()


def format_cart(items: list[dict]) -> str:
    if not items:
        return "🛒 Ваша корзина пуста"
    total = sum(i["price"] * i["quantity"] for i in items)
    lines = ["🛒 <b>Ваша корзина:</b>\n"]
    for item in items:
        lines.append(f"• {item['name']} × {item['quantity']} = {item['price'] * item['quantity']:,.0f} ₽")
    lines.append(f"\n💰 <b>Итого: {total:,.0f} ₽</b>")
    return "\n".join(lines)


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message):
    items = await get_cart(message.from_user.id)
    text = format_cart(items)
    if items:
        await message.answer(text, reply_markup=cart_keyboard(items))
    else:
        await message.answer(text)


@router.callback_query(F.data.startswith("addcart:"))
async def add_to_cart_handler(call: CallbackQuery):
    product_id = int(call.data.split(":")[1])
    await add_to_cart(call.from_user.id, product_id)
    await call.answer("✅ Товар добавлен в корзину!")


@router.callback_query(F.data.startswith("removecart:"))
async def remove_from_cart_handler(call: CallbackQuery):
    product_id = int(call.data.split(":")[1])
    await remove_from_cart(call.from_user.id, product_id)
    items = await get_cart(call.from_user.id)
    text = format_cart(items)
    if items:
        await call.message.edit_text(text, reply_markup=cart_keyboard(items))
    else:
        await call.message.edit_text(text)
    await call.answer("Удалено")


@router.callback_query(F.data == "clearcart")
async def clear_cart_handler(call: CallbackQuery):
    await clear_cart(call.from_user.id)
    await call.message.edit_text("🗑 Корзина очищена")
    await call.answer()
