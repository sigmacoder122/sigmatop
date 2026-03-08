import asyncio
import logging
import aiosqlite
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ChatJoinRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# ================= НАСТРОЙКИ =================
BOT_TOKEN = "8210571030:AAGozAnLRuUhsWUItsL9OrFVxytX1bXS8NA"

# Канал №1 (Подписка)
CHANNEL_SUB_ID = -1002788463921
CHANNEL_SUB_URL = "https://t.me/eelge"

# Канал №2 (Заявка)
CHANNEL_REQ_ID = -1003880311711
CHANNEL_REQ_URL = "https://t.me/+tegJk-t5-YVhYWI0"

ADMIN_ID = 7658738825

logging.basicConfig(level=logging.INFO)

# Включаем HTML по умолчанию для красивого форматирования!
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()
dp.include_router(router)

album_cache = {}


# ================= СОСТОЯНИЯ =================
class UserFunnel(StatesGroup):
    waiting_for_task = State()
    waiting_for_screenshots = State()


class Admin(StatesGroup):
    waiting_for_broadcast = State()


# ================= БАЗА ДАННЫХ =================
async def init_db():
    async with aiosqlite.connect('bot_database.db') as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users (
                            user_id INTEGER PRIMARY KEY,
                            username TEXT,
                            status TEXT DEFAULT 'started',
                            requested_join INTEGER DEFAULT 0
                        )''')
        await db.commit()


async def add_or_update_user(user_id: int, username: str, status: str = 'started'):
    async with aiosqlite.connect('bot_database.db') as db:
        await db.execute('''INSERT INTO users (user_id, username, status) 
                            VALUES (?, ?, ?) 
                            ON CONFLICT(user_id) DO UPDATE SET username = ?''',
                         (user_id, username, status, username))
        await db.commit()


async def mark_join_request(user_id: int):
    async with aiosqlite.connect('bot_database.db') as db:
        await db.execute('UPDATE users SET requested_join = 1 WHERE user_id = ?', (user_id,))
        await db.commit()


async def check_if_requested(user_id: int) -> bool:
    async with aiosqlite.connect('bot_database.db') as db:
        async with db.execute('SELECT requested_join FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] == 1 if row else False


# ================= ЛОГИКА БОТА =================

# 1. Команда /start - ИГРА "ИСПЫТАЙ УДАЧУ"
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await add_or_update_user(message.from_user.id, message.from_user.username)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏀 Испытать удачу", callback_data="play_basketball")]
    ])

    # Добавил красивые цитаты в приветствие!
    await message.answer(
        "👋 <b>Добро пожаловать!</b>\n\n"
        "<blockquote>Готов проверить свою меткость и получить доступ к секретным заданиям?</blockquote>\n\n"
        "👇 <i>Жми кнопку ниже, чтобы сделать бросок!</i>",
        reply_markup=keyboard
    )
    await state.clear()


# 2. Обработка игры и выдача меню подписки
@router.callback_query(F.data == "play_basketball")
async def play_game(call: CallbackQuery, state: FSMContext):
    await call.answer()

    await call.message.edit_reply_markup(reply_markup=None)

    # Бот крутит рулетку, пока не выпадет попадание
    while True:
        dice_msg = await bot.send_dice(chat_id=call.message.chat.id, emoji="🏀")

        if dice_msg.dice.value >= 4:
            break
        else:
            try:
                await bot.delete_message(chat_id=call.message.chat.id, message_id=dice_msg.message_id)
            except Exception:
                pass
            await asyncio.sleep(0.1)

    # Ждем 4 секунды (время анимации полета мяча)
    await asyncio.sleep(4)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Основной канал (Подписка)", url=CHANNEL_SUB_URL)],
        [InlineKeyboardButton(text="🔒 Закрытый канал (Заявка)", url=CHANNEL_REQ_URL)],
        [InlineKeyboardButton(text="✅ Проверить выполнение", callback_data="check_all")]
    ])

    text = (
        "🎉 <b>Вот это бросок! Ты попал, молодец! Доступ открыт!</b>\n\n"
        "<blockquote>Для получения подарка подпишитесь на спонсоров</blockquote>\n\n"
        "👇 <b>Выполните два простых шага:</b>\n"
        "<b>1.</b> Подпишитесь.\n"
        "<b>2.</b> Подайте заявку.\n\n"
        "<i>Как только сделаете — нажимайте кнопку проверки!</i>"
    )

    await call.message.answer(text, reply_markup=keyboard)
    await state.set_state(UserFunnel.waiting_for_task)


# 3. Ловим заявку на вступление
@router.chat_join_request()
async def handle_join_request(update: ChatJoinRequest):
    if update.chat.id == CHANNEL_REQ_ID:
        await add_or_update_user(update.from_user.id, update.from_user.username)
        await mark_join_request(update.from_user.id)


# 4. Проверка условий и выдача задания
@router.callback_query(F.data == "check_all")
async def check_conditions(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    try:
        sub_member = await bot.get_chat_member(chat_id=CHANNEL_SUB_ID, user_id=user_id)
        is_subscribed = sub_member.status in ['member', 'administrator', 'creator']
        has_requested = await check_if_requested(user_id)

        if is_subscribed and has_requested:
            text = (
                "🎉 <b>Условия выполнены!</b>\n\n"
                "<blockquote>Внимательно ознакомьтесь с инструкцией ниже. От точности выполнения зависит успешность проверки.</blockquote>\n\n"
                "📱 <b>Платформа:</b> TikTok\n"
                "🎯 <b>Задача:</b> Оставить 5 комментариев под разными видео.\n\n"
                "📝 <b>Текст комментария</b> <i>(нажмите, чтобы скопировать)</i>:\n"
                "<code>vovnnbot реально топ</code>\n\n"
                "📸 <b>Как сдать отчет:</b>\n"
                "Сделайте 5 скриншотов ваших комментариев и отправьте их сюда <b>ОДНИМ СООБЩЕНИЕМ</b> (в виде альбома)."
            )
            await call.message.edit_text(text)
            await state.set_state(UserFunnel.waiting_for_screenshots)
        else:
            if not is_subscribed and not has_requested:
                await call.answer("❌ Вы не подписались на первый канал и не подали заявку во второй!", show_alert=True)
            elif not is_subscribed:
                await call.answer("❌ Вы не подписались на открытый канал!", show_alert=True)
            elif not has_requested:
                await call.answer("❌ Вы не подали заявку в закрытый канал!", show_alert=True)

    except TelegramBadRequest:
        await call.answer("❌ Техническая ошибка. Бот должен быть администратором в обоих каналах.", show_alert=True)


# 5. Прием скриншотов
@router.message(F.photo, UserFunnel.waiting_for_screenshots)
async def handle_screenshots(message: Message, state: FSMContext):
    if message.media_group_id:
        if message.media_group_id in album_cache:
            return
        album_cache[message.media_group_id] = True

    async with aiosqlite.connect('bot_database.db') as db:
        await db.execute("UPDATE users SET status = 'completed' WHERE user_id = ?", (message.from_user.id,))
        await db.commit()

    text = (
        "✅ <b>Отчет успешно принят!</b>\n\n"
        "<blockquote>Ваша заявка отправлена на модерацию. Мы проверим скриншоты в порядке очереди.</blockquote>\n\n"
        "<i>Спасибо за участие! Вы можете следить за новостями в наших каналах.</i>"
    )
    await message.answer(text)
    await state.clear()


# ================= АДМИН-ПАНЕЛЬ И РАССЫЛКА =================

@router.message(Command("stats"))
async def get_stats(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    async with aiosqlite.connect('bot_database.db') as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total = (await cursor.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE status = 'completed'") as cursor:
            completed = (await cursor.fetchone())[0]

    text = (
        "📊 <b>Статистика бота:</b>\n\n"
        f"👥 Всего пользователей: <b>{total}</b>\n"
        f"✅ Выполнили задание: <b>{completed}</b>"
    )
    await message.answer(text)


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "📢 <b>Режим рассылки</b>\nОтправьте сообщение (текст, фото, видео), которое получат все пользователи:")
    await state.set_state(Admin.waiting_for_broadcast)


@router.message(StateFilter(Admin.waiting_for_broadcast))
async def process_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("⏳ <i>Начинаю рассылку...</i>")

    sent = 0
    blocked = 0
    async with aiosqlite.connect('bot_database.db') as db:
        async with db.execute("SELECT user_id FROM users") as cursor:
            users = await cursor.fetchall()

    for row in users:
        try:
            await message.copy_to(chat_id=row[0])
            sent += 1
            await asyncio.sleep(0.05)
        except TelegramForbiddenError:
            blocked += 1
        except Exception:
            pass

    await message.answer(
        f"✅ <b>Рассылка завершена!</b>\n\nУспешно доставлено: <b>{sent}</b>\nЗаблокировали бота: <b>{blocked}</b>")


# ================= ЗАПУСК =================
async def main():
    await init_db()
    print("Бот запущен!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())