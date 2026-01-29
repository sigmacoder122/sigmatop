from aiogram import BaseMiddleware, Bot, types
from aiogram.types import TelegramObject
from typing import Callable, Dict, Awaitable, Any
from config import CHANNEL_ID  # ID вашего канала
import logging


class SubscriptionMiddleware(BaseMiddleware):
    def __init__(self, bot: Bot):
        self.bot = bot
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")

        # Проверяем подписку для всех событий, кроме команды /start
        if not isinstance(event, types.Message) or (hasattr(event, "text") and event.text != '/start'):
            if user and not await self.check_subscription(user.id):
                await self.ask_for_subscription(event)
                return  # Прерываем обработку события

        return await handler(event, data)

    async def check_subscription(self, user_id: int) -> bool:
        try:
            member = await self.bot.get_chat_member(CHANNEL_ID, user_id)
            return member.status in ["member", "administrator", "creator"]
        except Exception as e:
            logging.error(f"Subscription check error: {e}")
            return True  # В случае ошибки разрешаем действие

    async def ask_for_subscription(self, event):
        text = (
            "📢В нашем боте самые низкие цены! По этому для использования бота необходимо подписаться на наш канал!\n"
            "После подписки нажмите кнопку 'Проверить подписку'."
        )
        markup = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🔔 Подписаться", url=f"https://t.me/eelge")],
            [types.InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check_subscription")]
        ])

        if isinstance(event, types.CallbackQuery):
            await event.message.answer(text, reply_markup=markup)
        elif isinstance(event, types.Message):
            await event.answer(text, reply_markup=markup)
        else:
            # Для других типов событий (например, inline-запросов)
            chat_id = event.from_user.id
            await self.bot.send_message(chat_id, text, reply_markup=markup)