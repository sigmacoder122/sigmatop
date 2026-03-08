import asyncio
import logging
import os
import sys  # Добавлен для запуска второго файла
import aiohttp
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.client.default import DefaultBotProperties

from config import TOKEN
from app.handlers import router
from app.database.models import async_main
from app.middlewares import SubscriptionMiddleware


async def self_ping():
    """Пинг самого себя каждые 10 минут, чтобы не засыпать"""
    url = "https://sigmatop.onrender.com"
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    logging.info(f"Self-ping: {resp.status}")
        except Exception as e:
            logging.error(f"Self-ping error: {e}")
        await asyncio.sleep(600)


# ПРОСТАЯ ЗАГЛУШКА ДЛЯ ВСЕХ ЗАПРОСОВ
async def handle_all_requests(request):
    """
    Универсальный обработчик для любых запросов
    Просто говорит, что бот работает
    """
    return web.Response(text="✅ Бот работает! Сервер запущен.")


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота / Главное меню")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


# ФУНКЦИЯ ДЛЯ ЗАПУСКА ВТОРОГО БОТА (ppp.py)
# ФУНКЦИЯ ДЛЯ ЗАПУСКА ВТОРОГО БОТА (ppp.py)
async def run_ppp_bot():
    """Фоновый запуск скрипта ppp.py"""

    # 1. Получаем точный путь к файлу, чтобы сервер точно его нашел
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ppp_path = os.path.join(current_dir, 'ppp.py')

    if not os.path.exists(ppp_path):
        logging.error(f"❌ ФАЙЛ НЕ НАЙДЕН: {ppp_path}. Убедись, что он лежит в той же папке!")
        return

    logging.info("🚀 Запускаем второго бота (ppp.py)...")

    # 2. Флаг '-u' заставляет Python выдавать логи сразу, без задержек (буферизации)
    process = await asyncio.create_subprocess_exec(
        sys.executable, '-u', ppp_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Функция для перехвата и вывода логов от ppp.py
    async def read_stream(stream, prefix):
        while True:
            line = await stream.readline()
            if not line:
                break
            print(f"{prefix}: {line.decode('utf-8').strip()}")

    # Читаем логи в фоне
    asyncio.create_task(read_stream(process.stdout, "🏀 [PPP]"))
    asyncio.create_task(read_stream(process.stderr, "❌ [PPP ERROR]"))

    # 3. ВАЖНО: заставляем основную программу следить за этим процессом
    await process.wait()
    logging.warning("⚠️ Процесс ppp.py завершил свою работу!")


async def main():
    await async_main()

    # Инициализация бота
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    # 🔥 ВАЖНО: сбрасываем вебхуки
    await bot.delete_webhook(drop_pending_updates=True)

    dp = Dispatcher()

    # Регистрация мидлварей
    dp.message.middleware.register(SubscriptionMiddleware(bot))
    dp.callback_query.middleware.register(SubscriptionMiddleware(bot))
    dp.inline_query.middleware.register(SubscriptionMiddleware(bot))

    dp.include_router(router)

    await set_commands(bot)

    # === ВЕБ-СЕРВЕР-ЗАГЛУШКА ===
    app = web.Application()
    app.router.add_route('*', '/{tail:.*}', handle_all_requests)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"🌐 Сервер-заглушка запущен на порту {port}")

    # === ЗАПУСК САМОПИНГА ===
    asyncio.create_task(self_ping())
    logging.info("🔄 Самопинг запущен (каждые 10 минут)")

    # === ЗАПУСК ВТОРОГО БОТА ===
    asyncio.create_task(run_ppp_bot())

    # Запуск поллинга основного бота
    logging.info("🤖 Основной бот начал поллинг сообщений...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")