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

# Налаштування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Перевірка токенів
TELEGRAM_TOKEN = "7738138408:AAEMrBTn7b-G4I483n_f2b7ceKhl2eSRkdQ"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    logger.error("❌ Telegram token not found!")
    exit(1)

if not OPENAI_API_KEY:
    logger.warning("⚠️ OpenAI key not found - some functions will be disabled")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# База даних
def get_db():
    return sqlite3.connect('/tmp/bot.db' if 'RENDER' in os.environ else 'bot.db')

conn = get_db()
cursor = conn.cursor()

# Ініціалізація БД
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

# Команди
@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    
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
    
    await message.answer("🏫 Вітаю у Шкільному помічнику!", reply_markup=get_main_keyboard())

@dp.message(Command('kontrolni'))
async def cmd_kontrolni(message: types.Message):
    task = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if not task:
        return await message.answer("📝 Напишіть завдання після команди")
    
    response = await generate_ai_response(f"Розв'яжи контрольну роботу: {task}", 'uk')
    await message.answer(f"📚 Розв'язок:\n{response}")

@dp.message(Command('gen_image'))
async def cmd_gen_image(message: types.Message):
    prompt = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if not prompt:
        return await message.answer("ℹ️ Напишіть опис зображення після команди")
    
    image_url, error = await generate_image(message.from_user.id, prompt)
    if error:
        return await message.answer(error)
    
    await message.answer_photo(image_url)

@dp.message(Command('shawarma'))
async def cmd_shawarma(message: types.Message):
    facts = [
        "Шаурма - це найкращий антидепресант!",
        "Науковці довели: шаурма містить вітамін щастя",
        "Без шаурми неможливо уявити студентське життя",
        "Шаурма об'єднує народи - це факт міжнародної дипломатії"
    ]
    await message.answer(random.choice(facts))

# Допоміжні функції
async def generate_ai_response(prompt: str, lang: str) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message['content']

# Запуск бота
async def on_startup():
    await reset_daily_limits()

async def reset_daily_limits():
    cursor.execute(
        "UPDATE limits SET images_left = 100, audio_left = 100, circles_left = 100 "
        "WHERE last_reset_date < ?",
        (datetime.now().date().isoformat(),)
    )
    conn.commit()

if __name__ == '__main__':
    dp.startup.register(on_startup)
    dp.run_polling(bot, skip_updates=True)