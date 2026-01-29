import asyncio
import random
import string
import warnings
from telethon import TelegramClient
from telethon.tl.functions.account import CheckUsernameRequest
from telethon.errors import FloodWaitError

# Подавляем предупреждения Telethon про экспериментальные сессии
warnings.filterwarnings("ignore", category=UserWarning)

api_id = 22568221
api_hash = 'dffa9a65f40aa5cfbbffe88b6f30edcb'

# 📨 Кому отправлять найденные свободные ники
target_user = "qvvor"

# Имена файлов для сессий
sessions = ["session1", "session2"]


# 🔠 Генератор никнеймов (5 букв, 2 пары одинаковых символов)
# 🔠 Генератор никнеймов (3 одинаковых + 2 одинаковых других)
def generate_username():
    letters = string.ascii_lowercase

    # выбираем 2 разные буквы
    a, b = random.sample(letters, 2)

    # собираем список: три буквы a и две буквы b
    chars = [a] * 3 + [b] * 2

    # перемешиваем
    random.shuffle(chars)
    return "".join(chars)



async def worker(session_name: str, delay_start: int):
    """Один воркер (одна сессия Telegram)"""
    await asyncio.sleep(delay_start)  # старт с задержкой

    async with TelegramClient(session_name, api_id, api_hash) as client:
        print(f"✅ {session_name} запущена")

        while True:
            username = generate_username()
            try:
                result = await client(CheckUsernameRequest(username))
                if result:
                    status = "✅ свободен"

                    # сохраняем в файл
                    with open("free_usernames.txt", "a", encoding="utf-8") as f:
                        f.write(f"{session_name} @{username}\n")

                    # отправляем пользователю
                    try:
                        await client.send_message(target_user, f"{session_name} 🎉 Свободный ник: @{username}")
                    except Exception as e:
                        print(f"{session_name} ⚠️ Ошибка отправки: {e}")

                else:
                    status = "❌ занят"

                # Выводим результат в консоль (2 столбика)
                print(f"{session_name:<10} @{username:<10} {status}")

            except FloodWaitError as e:
                print(f"{session_name} ⏳ FloodWait {e.seconds} сек")
                await asyncio.sleep(e.seconds + 5)

            except Exception as err:
                print(f"{session_name} ⚠️ Ошибка при {username}: {err}")

            # каждая сессия делает проверку раз в 40 секунд
            await asyncio.sleep(40)


async def main():
    # Запускаем 2 сессии параллельно
    await asyncio.gather(
        worker("session1", 0),   # старт сразу
        worker("session2", 1),
    )


if __name__ == "__main__":
    asyncio.run(main())
