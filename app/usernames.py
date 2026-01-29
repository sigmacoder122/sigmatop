from telethon import TelegramClient
import asyncio

# === НАСТРОЙКИ ===
# Получи api_id и api_hash здесь: https://my.telegram.org/auth
api_id = 6062313478  # <-- замени на свой api_id
api_hash = "27aa2877c81471a11e0383ea111ed0a5a61191c63ec794b8d30b1ad17c7c09c5f16e1a29460f709b82bbea5cda60649904190794a6a0c6ac1396b19bbd274a6f08cc51d80edb18b851865cff053b7cc0977279b9b7e1785a6461f09c4ed7dfbafae9fef8e5b9507c5ec31f35df184b0862c5e9851283de3018bfc51531fa7fa2fd9c3b85075bded770aa1ca6230b0aa23017766a4bf3d77f6a66be0c2bdd678fa11b18f70603cef765035705405f533c7edc89f03443f5ef8d374831531b6747cb294d60e31a265220341384e95284f71d546a8801eb9bb5c2a9abfad93b2b35919171436b9afb41e6d130b78716058aa6a80d3a7eaace2f67db2f4c31f7c47c"  # <-- замени на свой api_hash

# Список ников для проверки
usernames = [
    "zorvi", "klyvo", "jivor", "qvix", "lfyro",
    "mavro", "nuvra", "zlyon", "jexo", "tovoq"
]

async def main():
    async with TelegramClient("checker", api_id, api_hash) as client:
        for u in usernames:
            try:
                result = await client.get_entity(u)
                print(f"@{u} ❌ занят ({result.__class__.__name__})")
            except:
                print(f"@{u} ✅ свободен")

if __name__ == "__main__":
    asyncio.run(main())
