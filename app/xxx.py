import asyncio
import random
import warnings
from telethon import TelegramClient, errors
from telethon.tl import functions

# Подавляем предупреждения Telethon про экспериментальные сессии
warnings.filterwarnings("ignore", category=UserWarning)

api_id = 28840417
   # твой api_id
api_hash = 'b20ed29da07d82dbedb2c8e8dd91b281'  # твой api_hash
receiver = "qvvor"  # пользователь, которому отправлять свободные username

client = TelegramClient("check_usernames", api_id, api_hash)

usernames = [
    # 1) Редкие английские слова/фразы
    'зvjjvioene424',"unbrokensociety", "silentwhisper", "frostedmoon", "velvetdawn", "crimsonleaf",
    "goldenhaze", "mysticriver", "hiddenrealm", "fabledforest", "stormyknight",
    "shadowpulse", "emeraldsky", "twilightsong", "wanderlusting", "phantomlight",
    "luminouspath", "dreamcatcher", "echoingvalley", "gildedhorizon", "whisperwind",

    # 2) Красивые сочетания букв (до 5 символов)
    "qvtrz", "blimx", "xoryp", "fjlkd", "zaphy", "trixs",
    "mynqv", "vlewp", "soprk", "klivn", "jynxo", "quopy",
    "glimt", "vradx", "tusky", "plowz", "skivq", "barky",
    "florp", "nexum", "wyndq", "crypz", "zoltx", "grixv",
    "lophk", "frenq", "blory", "draxv", "mylop", "vornq",
    "plaxy", "truvk", "qorpx", "zymlt", "kluvq", "fronz",
    "blikt", "dravy", "squor", "vynix", "tropl", "qufry",
    "glozn", "privy", "zomax", "jilto", "cravn", "fynex",
    "blowy", "trenk", "vupix", "qylor",

    # 3) Новые русские слова транслитом (без цифр и повторов)
    "golubka", "berezhok", "ryabinka", "sosnovka", "topolka", "jasminok", "orenka",
    "dolinok", "bukovka", "rybinka", "kamenok", "pesochok", "granitoch", "prolivok",
    "ozernik", "ruslochka", "vodopadik", "priboyok", "lesochek", "sosenka",
    "topolok", "akacinka", "orelochka", "malinovka", "klubnichka", "slivka",
    "vinogradik", "yablonechka", "ogurechnik", "kabachok", "borshchik", "kashka",
    "perechik", "chernichka", "filionok", "kotletka", "teplitsa", "morozik",
    "tumanchik", "dubyok", "orehok", "yagodnik", "malinovik", "klubnichnik",
    "romashkovik", "vasilechnik", "podsolnichik", "kapustnik", "morkovichok",
    "gribovich", "medvezhonik", "lisichik", "zayachik", "golubochka", "vorobushok",
    "lastochik", "sovushka", "drozdik", "utyonok", "gusik", "volchok", "barsuchok",
    "ezhik", "belchik", "mishutka", "kotenok", "sharichok", "pusichok", "lapochik"
]


async def check_usernames(usernames):
    await client.start()
    results = {}
    for username in usernames:
        try:
            available = await asyncio.wait_for(
                client(functions.account.CheckUsernameRequest(username)),
                timeout=5
            )
            status = "✅ Свободен" if available else "❌ Занят"
            print(f"{username}: {status}")
            results[username] = status

            # Если свободен — отправляем в чат qvvor
            if available:
                await client.send_message(receiver, f"Свободный username: {username}")

        except errors.FloodWaitError as e:
            print(f"{username}: ⚠ Flood wait {e.seconds} секунд, пропускаем...")
            results[username] = f"Flood wait {e.seconds} секунд"
            continue
        except (asyncio.TimeoutError, errors.RPCError) as e:
            print(f"{username}: ⚠ Ошибка ({e}), пропускаем...")
            results[username] = f"Ошибка: {e}"
        except Exception as e:
            print(f"{username}: ⚠ Неизвестная ошибка ({e})")
            results[username] = f"Ошибка: {e}"

        # случайная задержка 5–10 секунд
        await asyncio.sleep(random.uniform(10, 10))
    return results

async def main():
    await check_usernames(usernames)

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
