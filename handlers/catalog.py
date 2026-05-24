from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database import get_categories, get_products, get_product
from keyboards.kb import categories_keyboard, products_keyboard, product_keyboard

router = Router()


@router.message(F.text == "🛍 Каталог")
async def show_catalog(message: Message):
    categories = await get_categories()
    if not categories:
        await message.answer("😔 Каталог пока пуст")
        return
    await message.answer(
        "📂 <b>Выберите категорию:</b>",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data == "back:catalog")
async def back_to_catalog(call: CallbackQuery):
    categories = await get_categories()
    await call.message.edit_text(
        "📂 <b>Выберите категорию:</b>",
        reply_markup=categories_keyboard(categories)
    )


@router.callback_query(F.data.startswith("cat:"))
async def show_category(call: CallbackQuery):
    category = call.data.split(":", 1)[1]
    products = await get_products(category)
    if not products:
        await call.answer("В этой категории нет товаров", show_alert=True)
        return
    await call.message.edit_text(
        f"🛍 <b>{category}</b>\n\nВыберите товар:",
        reply_markup=products_keyboard(products, category)
    )


@router.callback_query(F.data.startswith("product:"))
async def show_product(call: CallbackQuery):
    product_id = int(call.data.split(":")[1])
    product = await get_product(product_id)
    if not product:
        await call.answer("Товар не найден", show_alert=True)
        return

    text = (
        f"<b>{product['name']}</b>\n\n"
        f"📝 {product['description'] or 'Нет описания'}\n\n"
        f"💰 Цена: <b>{product['price']:,.0f} ₽</b>\n"
        f"✅ В наличии"
    )

    await call.message.edit_text(
        text,
        reply_markup=product_keyboard(product_id, product["category"])
    )
