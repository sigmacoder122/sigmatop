from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_ID
import database.db as db
from keyboards.inline import get_admin_kb # Сейчас создадим её

router = Router()

@router.message(Command("admin"))
async def admin_main(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    stats = await db.get_admin_stats()
    reward = await db.get_reward()

    text = (
        "⚙️ <b>ПАНЕЛЬ УПРАВЛЕНИЯ АДМИНИСТРАТОРА</b>\n\n"
        "<blockquote>Здесь вы можете изменять настройки выплат и смотреть общую статистику проекта в реальном времени.</blockquote>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"┣ 👥 Всего пользователей: <code>{stats['total_users']}</code>\n"
        f"┗ 💰 Общий баланс: <code>{stats['total_balance']} ₽</code>\n\n"
        f"💸 <b>Текущая выплата:</b> <code>{reward} ₽</code> за вход"
    )
    await message.answer(text, reply_markup=get_admin_kb(), parse_mode="HTML")