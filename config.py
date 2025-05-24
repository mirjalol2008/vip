import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # O'zingizning Telegram ID'ingiz
VIP_CHANNEL_ID = int(os.getenv("VIP_CHANNEL_ID", "-1002424516355"))  # Private channel ID

# Card info post link (admin panelda o'zgartiriladi)
CARD_INFO_LINK = "https://t.me/vipmangainfo/2"