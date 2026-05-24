from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command

from config import ADMIN_IDS, SUPPORT_USERNAME
from database import upsert_user
from keyboards.kb import main_menu, admin_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    await upsert_user(user.id, user.username or "", user.full_name)

    is_admin = user.id in ADMIN_IDS
    kb = admin_menu() if is_admin else main_menu()

    await message.answer(
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        f"Добро пожаловать в наш магазин.\n"
        f"Здесь ты найдёшь лучшие товары по отличным ценам.\n\n"
        f"Выбери раздел в меню 👇",
        reply_markup=kb
    )


@router.message(F.text == "ℹ️ О магазине")
async def about(message: Message):
    await message.answer(
        "🏪 <b>О нашем магазине</b>\n\n"
        "Мы продаём качественные товары с быстрой доставкой.\n\n"
        "📦 Доставка: 1-3 дня\n"
        "💳 Оплата: при получении или переводом\n"
        "🔄 Возврат: в течение 14 дней\n\n"
        f"📞 Поддержка: {SUPPORT_USERNAME}"
    )
