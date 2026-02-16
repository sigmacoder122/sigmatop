import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.client.default import DefaultBotProperties  # Добавили этот импорт

from config import TOKEN
from app.handlers import router
from app.database.models import async_main
from app.middlewares import SubscriptionMiddleware



async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🚀 Запустить бота / Главное меню")


    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


async def main():
    await async_main()

    # Инициализация бота с новыми правилами aiogram 3.7+
    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")  # Теперь это пишется так
    )

    dp = Dispatcher()

    # Регистрация мидлварей
    dp.message.middleware.register(SubscriptionMiddleware(bot))
    dp.callback_query.middleware.register(SubscriptionMiddleware(bot))
    dp.inline_query.middleware.register(SubscriptionMiddleware(bot))

    dp.include_router(router)

    await set_commands(bot)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")