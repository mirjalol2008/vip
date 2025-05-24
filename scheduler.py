import asyncio
from datetime import datetime
from database import get_all_subscriptions, remove_subscription
from aiogram import Bot
from config import API_TOKEN, VIP_CHANNEL_ID

bot = Bot(token=API_TOKEN)

async def check_expired_subs():
    while True:
        now = datetime.now()
        for sub in get_all_subscriptions():
            user_id, until = sub
            if until < now:
                try:
                    await bot.kick_chat_member(VIP_CHANNEL_ID, user_id)
                    remove_subscription(user_id)
                    print(f"{user_id} VIP kanaldan chiqarildi.")
                except Exception as e:
                    print(f"Xatolik: {e}")
        await asyncio.sleep(60)