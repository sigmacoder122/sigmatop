import asyncio
import logging
import os
from aiohttp import web

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.client.default import DefaultBotProperties

from config import TOKEN
from app.handlers import router
from app.database.models import async_main
from app.middlewares import SubscriptionMiddleware


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


async def main():
    await async_main()

    # Инициализация бота
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )

    dp = Dispatcher()

    # Регистрация мидлварей
    dp.message.middleware.register(SubscriptionMiddleware(bot))
    dp.callback_query.middleware.register(SubscriptionMiddleware(bot))
    dp.inline_query.middleware.register(SubscriptionMiddleware(bot))

    dp.include_router(router)

    await set_commands(bot)

    # === МИНИМАЛЬНЫЙ ВЕБ-СЕРВЕР ДЛЯ RENDER ===
    app = web.Application()

    # Универсальный обработчик для ЛЮБОГО пути
    # Это заглушка - она отвечает на все запросы, включая проверки Render
    app.router.add_route('*', '/{tail:.*}', handle_all_requests)

    runner = web.AppRunner(app)
    await runner.setup()

    # Берем порт из переменной окружения Render
    port = int(os.environ.get('PORT', 8080))

    # Запускаем сервер
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logging.info(f"🌐 Сервер-заглушка запущен на порту {port}")
    logging.info("   📍 Render теперь видит открытый порт и не выдает ошибок")
    logging.info("   📍 Вебхуки Platega пока отключены (заглушка)")
    # ==========================================

    # Запуск поллинга бота
    logging.info("🤖 Бот начал поллинг сообщений...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен")