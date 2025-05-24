import aiosqlite
import datetime

DB_PATH = "botdata.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                expire_date TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bans (
                user_id INTEGER PRIMARY KEY,
                ban_until TEXT
            )
        """)
        await db.commit()

async def add_subscription(user_id: int, months: int):
    expire_date = datetime.datetime.utcnow() + datetime.timedelta(days=30*months)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO subscriptions (user_id, expire_date)
            VALUES (?, ?)
        """, (user_id, expire_date.isoformat()))
        await db.commit()

async def get_subscription_expire(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT expire_date FROM subscriptions WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return datetime.datetime.fromisoformat(row[0])
            return None

async def add_ban(user_id: int, ban_seconds: int = 86400):
    ban_until = datetime.datetime.utcnow() + datetime.timedelta(seconds=ban_seconds)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR REPLACE INTO bans (user_id, ban_until)
            VALUES (?, ?)
        """, (user_id, ban_until.isoformat()))
        await db.commit()

async def get_ban_time_left(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT ban_until FROM bans WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                ban_until = datetime.datetime.fromisoformat(row[0])
                now = datetime.datetime.utcnow()
                if ban_until > now:
                    return (ban_until - now).total_seconds()
                else:
                    # Ban muddati tugagan, uni o'chiramiz
                    await remove_ban(user_id)
                    return 0
            return 0

async def remove_ban(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM bans WHERE user_id = ?", (user_id,))
        await db.commit()