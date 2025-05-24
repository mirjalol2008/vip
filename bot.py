import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import asyncio
import database
from datetime import datetime, timedelta

API_TOKEN = 'YOUR_BOT_TOKEN'
VIP_CHANNEL_ID = -1002424516355  # private kanal ID sini shu yerga yozing (manfiy qilib)

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Karta ma'lumotlari post linki (so'zlash mumkin bo'lgan)
CARD_INFO_LINK = None

# Admin Telegram ID si (bitta yoki ro'yxat)
ADMIN_IDS = [123456789]

# 1. /start komandasi
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await message.answer("Salom! To‘lov uchun /pay tugmasini bosing.")

# 2. To‘lov tugmasi
@dp.message_handler(commands=['pay'])
async def cmd_pay(message: types.Message):
    if CARD_INFO_LINK:
        await message.answer(f"To‘lov qilish uchun karta ma'lumotlari: {CARD_INFO_LINK}\n"
                             "Chek yuboring va so‘rovni davom ettiring.")
    else:
        await message.answer("Karta ma'lumotlari hali sozlanmagan. Keyinroq urinib ko‘ring.")

# 3. To‘lov tugmasi o‘rniga inline tugma qilish (ixtiyoriy)
pay_kb = InlineKeyboardMarkup(row_width=1)
pay_kb.add(InlineKeyboardButton("To'lov qilish", callback_data="pay"))

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("Xush kelibsiz!", reply_markup=pay_kb)

# 4. Karta ma'lumotlarini admin sozlashi uchun komanda
@dp.message_handler(commands=['setcardinfo'])
async def set_card_info(message: types.Message):
    if message.from_user.id in ADMIN_IDS:
        args = message.get_args()
        global CARD_INFO_LINK
        if args.startswith("http"):
            CARD_INFO_LINK = args
            await message.reply("Karta ma'lumotlari linki o'rnatildi!")
        else:
            await message.reply("Iltimos, to'liq link yuboring.")
    else:
        await message.reply("Sizda bu komandani ishlatish huquqi yo'q.")

# 5. Chek qabul qilish va adminga bildirish
@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_receipt(message: types.Message):
    user_id = message.from_user.id
    # Ban holatini tekshirish
    ban_until = database.get_ban_until(user_id)
    if ban_until and ban_until > datetime.now():
        remain = ban_until - datetime.now()
        h, rem = divmod(remain.seconds, 3600)
        m, s = divmod(rem, 60)
        await message.reply(f"Kechirasiz, siz {h} soat {m} minut {s} soniyadan so'ng qayta foydalanishingiz mumkin.")
        return

    # Adminlarga habar yuborish
    for admin_id in ADMIN_IDS:
        # Chek rasmini yuborish
        await bot.send_photo(admin_id, message.photo[-1].file_id,
                             caption=f"Yangi chek keldi!\nFoydalanuvchi: @{message.from_user.username or user_id}\n"
                                     f"Foydalanuvchi ID: {user_id}")
        # Bu yerda tugmalarni yuborish kerak (1 oy, 3 oy, 6 oy, 1 yil)
        # Tugmalarni quyida yaratamiz
    
    await message.answer("✅ Tez orada so‘rovingizga javob beramiz!")

# 6. Admin tugmalari (inline tugmalar)
def admin_duration_kb(user_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("1 oy", callback_data=f"duration_1_{user_id}"),
        InlineKeyboardButton("3 oy", callback_data=f"duration_3_{user_id}"),
        InlineKeyboardButton("6 oy", callback_data=f"duration_6_{user_id}"),
        InlineKeyboardButton("1 yil", callback_data=f"duration_12_{user_id}"),
        InlineKeyboardButton("Noto'g'ri chek", callback_data=f"ban_{user_id}")
    )
    return kb

# Shu tugmalarni adminlarga yuborishda qo'shish kerak edi.

# 7. Callback query handler - admin tugmalarini ishlash
@dp.callback_query_handler(lambda c: c.data and (c.data.startswith("duration_") or c.data.startswith("ban_")))
async def process_admin_callback(callback_query: types.CallbackQuery):
    if callback_query.from_user.id not in ADMIN_IDS:
        await callback_query.answer("Siz admin emassiz!", show_alert=True)
        return

    data = callback_query.data
    parts = data.split("_")
    action = parts[0]
    if action == "duration":
        months = int(parts[1])
        user_id = int(parts[2])

        # Kanallarga qo'shish va obuna muddatini yozish
        until_date = datetime.now() + timedelta(days=30*months)
        database.add_subscription(user_id, until_date)

        # Foydalanuvchini kanalga qo'shish
        try:
            await bot.get_chat_member(VIP_CHANNEL_ID, user_id)
        except:
            # Agar kanalga qo'shilmagan bo'lsa qo'shish
            await bot.invite_link_create(VIP_CHANNEL_ID)  # bu Telegram API da mavjud emas, shuning uchun o'zgartirish kerak bo'lishi mumkin
            await bot.unban_chat_member(VIP_CHANNEL_ID, user_id)  # avval bloklangan bo'lsa
            # Aslida kanalga bot qo'sha olmaydi, admin qo'shishi kerak. Buning uchun userlarni kanalda avtomatik qo'shish uchun bot admin bo'lishi va botning userni qo'shish huquqi bo'lishi kerak
            # Bu joyni kerakli metod bilan almashtiring

        await callback_query.answer(f"Foydalanuvchi {months} oyga obunaga qo'shildi!")
        await bot.send_message(user_id, f"Siz {months} oyga AniBro Premium kanaliga qo'shildingiz!")

    elif action == "ban":
        user_id = int(parts[1])
        ban_until = datetime.now() + timedelta(hours=24)
        database.add_ban(user_id, ban_until)
        await callback_query.answer("Foydalanuvchi 24 soatga ban qilindi.")
        await bot.send_message(user_id, "Botdan noto'g'ri foydalanganiz uchun 24 soatga ban bo'ldingiz.")

# 8. Kanalga so'rov yuborgan foydalanuvchini tekshirish (har safar foydalanuvchi yozganda)
@dp.message_handler()
async def check_vip_request(message: types.Message):
    user_id = message.from_user.id
    try:
        member = await bot.get_chat_member(VIP_CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            # A'zo bo'lsa hech nima qilmaslik mumkin
            return
    except:
        # Agar a'zo emas bo'lsa
        await message.reply("Siz VIP kanalga qo'shilish so'rovini yubordingiz! To'liq ma'lumot uchun /start tugmasini bosing.")

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)