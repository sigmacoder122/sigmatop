import aiosqlite

DB_NAME = "bot_database.db"


async def init_db():
    """Создает таблицы, если их нет."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                invites_count INTEGER DEFAULT 0,
                invited_by INTEGER
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                reward_per_invite INTEGER DEFAULT 10
            )
        ''')
        await db.execute('INSERT OR IGNORE INTO settings (id, reward_per_invite) VALUES (1, 10)')
        await db.commit()


async def add_user(user_id: int, username: str, invited_by: int = None):
    """Регистрирует пользователя и начисляет бонус пригласившему."""
    async with aiosqlite.connect(DB_NAME) as db:
        # Проверяем, есть ли уже такой юзер
        async with db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)) as cursor:
            if await cursor.fetchone():
                return False  # Пользователь уже есть в базе

        # Добавляем нового пользователя
        await db.execute(
            "INSERT INTO users (user_id, username, invited_by) VALUES (?, ?, ?)",
            (user_id, username, invited_by)
        )

        # Если пришел по ссылке — даем бонус рефоводу
        if invited_by:
            # Узнаем текущую награду из настроек
            async with db.execute("SELECT reward_per_invite FROM settings WHERE id = 1") as cursor:
                row = await cursor.fetchone()
                reward = row[0] if row else 10

            # Начисляем деньги и +1 к статистике приглашений
            await db.execute(
                "UPDATE users SET balance = balance + ?, invites_count = invites_count + 1 WHERE user_id = ?",
                (reward, invited_by)
            )

        await db.commit()
        return True


async def get_user(user_id: int):
    """Получает все данные пользователя для Личного кабинета."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row  # Чтобы обращаться к колонкам по именам (напр. row['balance'])
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchone()


async def get_admin_stats():
    """Собирает общую статистику для админа."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*), SUM(balance) FROM users") as cursor:
            row = await cursor.fetchone()
            return {"total_users": row[0], "total_balance": row[1] or 0}

async def update_reward(new_reward: int):
    """Меняет награду за реферала."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE settings SET reward_per_invite = ? WHERE id = 1", (new_reward,))
        await db.commit()

async def get_reward():
    """Получает текущую награду."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT reward_per_invite FROM settings WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 10