from aiogram import Bot, types, Router
from aiogram.types import Message
from aiogram.methods.refund_star_payment import RefundStarPayment
from aiogram.filters import Command
import logging

API_TOKEN = "7871705211:AAEXrHzaRsYUoxB2_yRk7VxmU_FQRuPBDuE"
bot = Bot(token=API_TOKEN)
router = Router()



@router.message(Command("ref"))
async def refund(message: types.Message):
    args = message.text.split()[1:]  # Получаем аргументы после команды
    if not args:
        await message.answer("❌ Укажите ID транзакции для возврата Stars.")
        return

    charge_id = args[0]  # ID платежа Stars
    user_id = message.from_user.id  # ID пользователя, который совершил оплату

    try:
        # Вызываем метод RefundStarPayment
        result: bool = await message.bot(RefundStarPayment(
            user_id=user_id,
            telegram_payment_charge_id=charge_id
        ))

        if result:
            await message.answer("✅ Stars успешно возвращены.")
        else:
            await message.answer("❌ Не удалось вернуть Stars. Проверьте ID транзакции.")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка при возврате Stars: {e}")

# Для запуска бота через polling
from aiogram import Dispatcher
import asyncio

dp = Dispatcher()
dp.include_router(router)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
