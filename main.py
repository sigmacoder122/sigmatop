import asyncio
import logging
from aiohttp import web  # Добавили импорт для веб-сервера

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.client.default import DefaultBotProperties

from config import TOKEN
from app.handlers import router
from app.database.models import async_main
from app.middlewares import SubscriptionMiddleware


# ⚠️ Не забудь импортировать сюда свои функции для работы с БД и админом:
# from app.database import requests as rq
# from app.utils import notify_admin  (или где она у тебя лежит)


async def handle_platega_webhook(request):
    """
    Функция, которая принимает POST-запросы от Platega
    """
    # Достаем объект бота, который мы положили в app при запуске сервера
    bot: Bot = request.app['bot']

    try:
        # Читаем JSON, который прислала Platega
        data = await request.json()
        logging.info(f"🔔 Получен вебхук от Platega: {data}")

        status = data.get("status")
        tx_id = data.get("id")
        payload_str = data.get("payload")  # Наша строка "IDюзера_IDтовара"

        # Если статус CONFIRMED и мы передавали payload
        if status == "CONFIRMED" and payload_str:
            # Разбиваем payload обратно на ID юзера и товара
            user_id_str, item_id_str = payload_str.split('_')
            user_id = int(user_id_str)
            item_id = item_id_str

            # Получаем товар из базы (раскомментируй импорт rq выше)
            # item = await rq.get_item_by_id(item_id)
            # if item:
            # 1. Отправляем товар юзеру
            # await bot.send_message(
            #     chat_id=user_id,
            #     text=f"✅ Оплата получена!\n\nВот ваш товар: {item.name}\nСпасибо за покупку!"
            # )

            # 2. Уведомляем админа
            # await notify_admin(
            #     bot=bot,
            #     order_id=f"order_{tx_id}",
            #     user_id=user_id,
            #     item_name=item.name,
            #     payment_method="Platega Webhook"
            # )

        # Обязательно возвращаем 200 OK, иначе Platega будет долбиться к нам снова и снова
        return web.Response(status=200, text="OK")

    except Exception as e:
        logging.error(f"❌ Ошибка при обработке вебхука Platega: {e}")
        return web.Response(status=500, text="Internal Server Error")


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

    # === НАСТРОЙКА ВЕБ-СЕРВЕРА ДЛЯ ВЕБХУКОВ ===
    app = web.Application()
    # Кладем бота в приложение, чтобы достать его в хэндлере вебхука
    app['bot'] = bot
    # Регистрируем маршрут, куда Platega будет слать POST-запросы
    app.router.add_post('/webhook/platega', handle_platega_webhook)

    runner = web.AppRunner(app)
    await runner.setup()
    # Сервер слушает все интерфейсы (0.0.0.0) на порту 8080
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logging.info("🌐 Веб-сервер запущен: жду вебхуки на http://0.0.0.0:8080/webhook/platega")
    # ==========================================

    # Запуск поллинга самого бота (должен быть в самом конце, т.к. он блокирует выполнение)
    logging.info("🤖 Бот начал поллинг сообщений...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")