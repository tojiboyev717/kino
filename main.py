import logging
from keep_alive import keep_alive  # Keep alive faylini import qilamiz
import json
import re
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
import os

API_TOKEN = '7692358431:AAGvQd0H9QVcfApimKW1DFmOmupe98qEMwg'
KANAL_USERNAME = '@FilmNewUz'  # kanal username @siz
ADMIN_ID = 6560139113  # faqat sizning Telegram ID
MOVIES_FILE = "movies.json"
USERS_FILE = "users.json"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot)

# Kinoni turgan kanal ID'si (shaxsiy kanal, bot admin bo‘lishi kerak)
KANAL_CHAT_ID = -1002851050884  # bu yerga o‘z kanal ID'ngizni yozing
KINO_MESSAGE_ID = 2  # o‘sha videoning message_id'si


# === Obuna tekshiruvchi funksiya ===
async def is_user_subscribed(user_id):
    try:
        member = await bot.get_chat_member(chat_id=KANAL_USERNAME,
                                           user_id=user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False


# === /start komandasi ===
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    if await is_user_subscribed(user_id):
        save_user(user_id)  # 🔥 Foydalanuvchini ro'yxatga olamiz
        full_name = message.from_user.full_name
        beautiful_name = f"<i><b>{full_name}</b></i>"
        await message.answer(
            f"✅ <b>Xush kelibsiz, {beautiful_name}!</b>\n\n"
            "🎬 Siz bu bot orqali kinolarni tartib bilan raqam orqali topishingiz va tomosha qilishingiz mumkin.\n"
            "ℹ️ Kino raqamini yozing, masalan: <code>1</code>")
    else:
        knopka = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(
                "🔗 Kanalga obuna bo‘lish",
                url=f"https://t.me/{KANAL_USERNAME.strip('@')}")
        ], [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")]])
        await message.answer(
            "❗ <b>Botdan foydalanish uchun quyidagi kanalga obuna bo‘ling:</b>",
            reply_markup=knopka)


# === Tekshirish tugmasi ishlovchisi ===
@dp.callback_query_handler(lambda c: c.data == "check_sub")
async def check_subscription(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if await is_user_subscribed(user_id):
        await callback_query.message.edit_text(
            f"✅ <b>Xush kelibsiz, {callback_query.from_user.full_name}!</b>")
    else:
        await callback_query.answer("❌ Hali obuna bo‘lmadingiz!",
                                    show_alert=True)


# === JSON bilan ishlash ===
def load_movies():
    try:
        with open(MOVIES_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}


def save_movies(data):
    with open(MOVIES_FILE, 'w') as f:
        json.dump(data, f, indent=2)


# ❗️BU joyda emas edi! Pastga chiqaryapmiz:
def load_users():
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []


def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)


@dp.message_handler(commands=['panel'])
async def panel_handler(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return

    users = load_users()
    movies = load_movies()

    await msg.answer(f"📊 <b>Admin Panel</b>\n\n"
                     f"👤 Foydalanuvchilar soni: <b>{len(users)}</b>\n"
                     f"🎬 Saqlangan kinolar: <b>{len(movies)}</b>")


# === Kino silkasini yuborganda (admin tomonidan) ===
@dp.message_handler(
    lambda msg: msg.text and msg.text.startswith('https://t.me/'))
async def handle_link(msg: types.Message):
    if msg.from_user.id != ADMIN_ID:
        return

    match = re.match(r'https://t\.me/([\w\d_]+)/(\d+)', msg.text.strip())
    if not match:
        await msg.answer("❌ Noto‘g‘ri format. Misol: https://t.me/kanal/123")
        return

    kanal_username = match.group(1)
    msg_id = int(match.group(2))

    try:
        # Kanaldan real chat_id ni olish (private kanal uchun zarur)
        chat = await bot.get_chat(f"@{kanal_username}")
        real_chat_id = chat.id
    except:
        await msg.answer("❌ Kanal topilmadi yoki bot kanalga admin emas.")
        return

    dp.temp_kino = {"chat_id": real_chat_id, "message_id": msg_id}
    await msg.answer(
        "✅ Kino silkasi qabul qilindi. Endi raqam yozing (masalan: 1)")


# === Admin raqam yozsa — saqlash ===
@dp.message_handler(lambda msg: msg.text.isdigit())
async def admin_save_or_user_request(msg: types.Message):
    text = msg.text.strip()
    user_id = msg.from_user.id

    if user_id == ADMIN_ID and hasattr(dp, "temp_kino"):
        # Admin — saqlayapti
        movies = load_movies()
        movies[text] = dp.temp_kino
        save_movies(movies)
        del dp.temp_kino
        await msg.answer(f"✅ Kino {text}-raqam ostida saqlandi.")
    else:
        # Oddiy foydalanuvchi — so‘rayapti
        movies = load_movies()
        kino = movies.get(text)
        if kino:
            await bot.copy_message(chat_id=msg.chat.id,
                                   from_chat_id=kino['chat_id'],
                                   message_id=kino['message_id'])
        else:
            await msg.answer("❌ Bunday raqamga kino topilmadi.")


if __name__ == '__main__':
    keep_alive()  # 🟢 Botni jonli saqlash
    executor.start_polling(dp, skip_updates=True)
