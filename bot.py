import os
import logging
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import openai
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from gtts import gTTS
from PIL import Image, ImageDraw
import io
import random
import requests
from deep_translator import GoogleTranslator

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Перевірка токенів
TOKEN = os.getenv("TOKEN", "").strip()
KEY = os.getenv("KEY", "").strip()

if not TOKEN or ":" not in TOKEN:
    logger.error("❌ Невірний Telegram токен! Формат: 123456789:ABCdef...")
    exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

if KEY:
    key = KEY
else:
    logger.warning("⚠️ OpenAI ключ відсутній - деякі функції обмежені")

# База даних
def get_db():
    return sqlite3.connect('/tmp/bot.db' if 'RENDER' in os.environ else 'bot.db')

conn = get_db()
cursor = conn.cursor()

# Ініціалізація таблиць
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    registered_at TEXT,
    banned_until TEXT,
    ban_reason TEXT,
    premium_until TEXT,
    language TEXT DEFAULT 'uk'
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS limits (
    user_id INTEGER PRIMARY KEY,
    images_left INTEGER DEFAULT 100,
    audio_left INTEGER DEFAULT 100,
    circles_left INTEGER DEFAULT 100,
    last_reset_date TEXT
)''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS promo_codes (
    code TEXT PRIMARY KEY,
    reward_type TEXT,
    reward_value TEXT,
    created_by INTEGER,
    uses_left INTEGER,
    expires_at TEXT
)''')

conn.commit()

# Константи
ADMINS = [1119767022]  # Ваш Telegram ID
LANGUAGES = {'uk': '🇺🇦 Українська', 'en': '🇬🇧 English'}

# Клавіатури
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton('/kontrolni 📝'),
        KeyboardButton('/gdz 📚'),
        KeyboardButton('/spusuvanna ✍️'),
        KeyboardButton('/promo 🎁'),
        KeyboardButton('/shawarma 🌯'),
        KeyboardButton('/help ❓')
    )
    return keyboard

def get_admin_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(
        KeyboardButton('/promo_create'),
        KeyboardButton('/promo_list'),
        KeyboardButton('/ban_user'),
        KeyboardButton('/unban_user')
    )
    return keyboard

# Генерація контенту
async def generate_image(user_id: int, prompt: str):
    cursor.execute("SELECT images_left FROM limits WHERE user_id=?", (user_id,))
    if cursor.fetchone()[0] <= 0:
        return None, "❌ Ліміт зображень вичерпано (100/день)"
    
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="512x512"
    )
    image_url = response['data'][0]['url']
    
    cursor.execute(
        "UPDATE limits SET images_left = images_left - 1 WHERE user_id=?",
        (user_id,)
    )
    conn.commit()
    
    return image_url, None

async def generate_audio(user_id: int, text: str, lang='uk'):
    cursor.execute("SELECT audio_left FROM limits WHERE user_id=?", (user_id,))
    if cursor.fetchone()[0] <= 0:
        return None, "❌ Ліміт аудіо вичерпано (100/день)"
    
    tts = gTTS(text=text, lang=lang)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    
    cursor.execute(
        "UPDATE limits SET audio_left = audio_left - 1 WHERE user_id=?",
        (user_id,)
    )
    conn.commit()
    
    return audio_buffer, None

async def generate_circle(user_id: int):
    cursor.execute("SELECT circles_left FROM limits WHERE user_id=?", (user_id,))
    if cursor.fetchone()[0] <= 0:
        return None, "❌ Ліміт кружечків вичерпано (100/день)"
    
    img = Image.new('RGB', (512, 512), color=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    draw = ImageDraw.Draw(img)
    draw.ellipse([(50, 50), (462, 462)], outline='white', width=10)
    
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    cursor.execute(
        "UPDATE limits SET circles_left = circles_left - 1 WHERE user_id=?",
        (user_id,)
    )
    conn.commit()
    
    return img_buffer, None

async def generate_ai_response(prompt: str, lang: str) -> str:
    if not OPENAI_API_KEY:
        return "OpenAI API ключ не налаштовано"
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message['content']

# Команди
@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        await message.answer("👑 Вітаю, адміне!", reply_markup=get_admin_keyboard())
    else:
        await message.answer("🏫 Вітаю у Шкільному помічнику!", reply_markup=get_main_keyboard())
    
    cursor.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (user_id, username, registered_at) VALUES (?, ?, ?)",
            (user_id, message.from_user.username, datetime.now().isoformat())
        )
        cursor.execute(
            "INSERT INTO limits (user_id, last_reset_date) VALUES (?, ?)",
            (user_id, datetime.now().isoformat())
        )
        conn.commit()

@dp.message(Command('kontrolni'))
async def cmd_kontrolni(message: types.Message):
    task = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if not task:
        return await message.answer("📝 Напишіть завдання після команди")
    
    response = await generate_ai_response(f"Розв'яжи контрольну роботу: {task}", 'uk')
    await message.answer(f"📚 Розв'язок:\n{response}")

@dp.message(Command('gdz'))
async def cmd_gdz(message: types.Message):
    task = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if not task:
        return await message.answer("📖 Напишіть предмет та номер завдання")
    
    response = await generate_ai_response(f"Напиши детальний розв'язок для: {task}", 'uk')
    await message.answer(f"📝 ГДЗ:\n{response}")

@dp.message(Command('spusuvanna'))
async def cmd_spusuvanna(message: types.Message):
    task = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if not task:
        return await message.answer("✍️ Опишіть завдання, з яким потрібна допомога")
    
    response = await generate_ai_response(f"Допоможи з виконанням: {task}", 'uk')
    await message.answer(f"💡 Підказка:\n{response}")

@dp.message(Command('gen_image'))
async def cmd_gen_image(message: types.Message):
    prompt = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if not prompt:
        return await message.answer("ℹ️ Напишіть опис зображення після команди")
    
    image_url, error = await generate_image(message.from_user.id, prompt)
    if error:
        return await message.answer(error)
    
    await message.answer_photo(image_url)

@dp.message(Command('gen_audio'))
async def cmd_gen_audio(message: types.Message):
    text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if not text:
        return await message.answer("ℹ️ Введіть текст для перетворення в аудіо")
    
    audio_buffer, error = await generate_audio(message.from_user.id, text)
    if error:
        return await message.answer(error)
    
    await message.answer_voice(audio_buffer)

@dp.message(Command('gen_circle'))
async def cmd_gen_circle(message: types.Message):
    img_buffer, error = await generate_circle(message.from_user.id)
    if error:
        return await message.answer(error)
    
    await message.answer_photo(img_buffer)

@dp.message(Command('shawarma'))
async def cmd_shawarma(message: types.Message):
    facts = [
        "Шаурма – це квинтесенція смаку Всесвіту!",
        "Науково доведено: шаурма покращує настрій на 127%",
        "Без шаурми неможливе існування людства. Це факт.",
        "Шаурма містить всі необхідні вітаміни для щастя"
    ]
    await message.answer(random.choice(facts))

@dp.message(Command('promo_create'), lambda message: message.from_user.id in ADMINS)
async def cmd_promo_create(message: types.Message):
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        return await message.answer("❌ Формат: /promo_create <тип> <значення> <використань>")
    
    promo_type = args[1]
    promo_value = args[2]
    uses = int(args[3]) if len(args) > 3 else 1
    
    import secrets
    code = secrets.token_hex(4).upper()
    
    cursor.execute(
        "INSERT INTO promo_codes VALUES (?, ?, ?, ?, ?, ?)",
        (code, promo_type, promo_value, message.from_user.id, uses, (datetime.now() + timedelta(days=30)).isoformat())
    )
    conn.commit()
    
    await message.answer(f"🎁 Промокод створено:\nКод: <code>{code}</code>\nТип: {promo_type}\nЗначення: {promo_value}")

@dp.message(Command('promo'))
async def cmd_promo_activate(message: types.Message):
    code = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if not code:
        return await message.answer("ℹ️ Введіть промокод після команди")
    
    cursor.execute(
        "SELECT * FROM promo_codes WHERE code = ? AND (uses_left > 0 OR uses_left IS NULL) AND expires_at > ?",
        (code, datetime.now().isoformat())
    )
    promo = cursor.fetchone()
    
    if not promo:
        return await message.answer("❌ Промокод не знайдено або протерміновано")
    
    reward_type, reward_value = promo[1], promo[2]
    user_id = message.from_user.id
    
    if reward_type == "images":
        cursor.execute(
            "UPDATE limits SET images_left = images_left + ? WHERE user_id = ?",
            (int(reward_value), user_id)
        )
        reward_text = f"🖼 +{reward_value} зображень"
    elif reward_type == "premium":
        cursor.execute(
            "UPDATE users SET premium_until = ? WHERE user_id = ?",
            ((datetime.now() + timedelta(days=int(reward_value))).isoformat(), user_id)
        )
        reward_text = f"🌟 Преміум на {reward_value} днів"
    else:
        reward_text = "🎁 Невідома нагорода"
    
    cursor.execute(
        "UPDATE promo_codes SET uses_left = uses_left - 1 WHERE code = ?",
        (code,)
    )
    cursor.execute(
        "INSERT OR IGNORE INTO activated_promos VALUES (?, ?, ?)",
        (user_id, code, datetime.now().isoformat())
    )
    conn.commit()
    
    await message.answer(f"🎉 Промокод активовано!\nОтримано: {reward_text}")

# Система обмежень
async def reset_daily_limits():
    cursor.execute(
        "UPDATE limits SET images_left = 100, audio_left = 100, circles_left = 100 "
        "WHERE last_reset_date < ?",
        (datetime.now().date().isoformat(),)
    )
    conn.commit()

# Запуск бота
async def on_startup():
    await reset_daily_limits()
    logger.info("🔄 Денні ліміти оновлено")

if __name__ == '__main__':
    dp.startup.register(on_startup)
    dp.run_polling(bot, skip_updates=True)