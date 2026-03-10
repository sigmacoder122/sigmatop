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
TOKENS = '8442407027:AAHrzmYyqlMYwOQMcIdxZIxhHzmo5G24cOs'

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


    # Функция для перехвата и вывода логов от ppp.py



async def main():
    await async_main()

    # Инициализация бота
    bot = Bot(
        token=TOKENS,
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


    # Запуск поллинга основного бота
    logging.info("🤖 Основной бот начал поллинг сообщений...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")