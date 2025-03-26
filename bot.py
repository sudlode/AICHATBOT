import os
import logging
import sqlite3
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.strategy import FSMStrategy
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import openai
import matplotlib.pyplot as plt
from gtts import gTTS
from PIL import Image, ImageDraw
import io
import random

# Налаштування
logging.basicConfig(level=logging.INFO)
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ініціалізація бота
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Підключення до БД
def get_db():
    if 'RENDER' in os.environ:
        db_path = '/tmp/bot.db'
    else:
        db_path = 'bot.db'
    return sqlite3.connect(db_path)

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
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS limits (
    user_id INTEGER PRIMARY KEY,
    images_left INTEGER DEFAULT 100,
    audio_left INTEGER DEFAULT 100,
    circles_left INTEGER DEFAULT 100,
    last_reset_date TEXT
)
''')

conn.commit()

# Константи
ADMINS = [1119767022]  # Ваш Telegram ID
LANGUAGES = {'uk': '🇺🇦 Українська', 'en': '🇬🇧 English'}

# Клавіатура
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='/kontrolni 📝'), KeyboardButton(text='/gdz 📚')],
            [KeyboardButton(text='/spusuvanna ✍️'), KeyboardButton(text='/promo 🎁')],
            [KeyboardButton(text='/shawarma 🌯'), KeyboardButton(text='/help ❓')]
        ],
        resize_keyboard=True
    )

# Обробник команди /start
@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        await message.answer("👑 Вітаю, адміне!")
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

# Обробник команди /kontrolni
@dp.message(Command('kontrolni'))
async def cmd_kontrolni(message: types.Message):
    task = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else None
    if not task:
        return await message.answer("📝 Напишіть завдання після команди")
    
    response = await generate_ai_response(f"Розв'яжи контрольну роботу: {task}", 'uk')
    await message.answer(f"📚 Розв'язок:\n{response}")

# Функція для генерації тексту через OpenAI
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