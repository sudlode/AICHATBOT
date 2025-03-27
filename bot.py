import os
import json
import random
import telebot
import requests
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment
from googlesearch import search
import pytesseract
from bs4 import BeautifulSoup
from io import BytesIO

# API ключі
TOKEN = os.getenv("TOKEN")  # Ваш токен для Telegram бота
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Ваш ключ для OpenAI

# Ініціалізація бота
bot = telebot.TeleBot(TOKEN)

# Ініціалізація вашого Telegram ID для активації адміністратора
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")  # Ваш ID для адміністратора

# Шлях до файлів для збереження історії, заблокованих користувачів та промокодів
history_file = "history.json"
banned_users_file = "banned_users.json"
promo_codes_file = "promo_codes.json"
statistics_file = "statistics.json"

# Завантаження історії
def load_history():
    if os.path.exists(history_file):
        with open(history_file, 'r') as file:
            return json.load(file)
    return {}

# Завантаження заблокованих користувачів
def load_banned_users():
    if os.path.exists(banned_users_file):
        with open(banned_users_file, 'r') as file:
            return json.load(file)
    return []

# Завантаження промокодів
def load_promo_codes():
    if os.path.exists(promo_codes_file):
        with open(promo_codes_file, 'r') as file:
            return json.load(file)
    return {}

# Завантаження статистики
def load_statistics():
    if os.path.exists(statistics_file):
        with open(statistics_file, 'r') as file:
            return json.load(file)
    return {"requests": 0, "bans": 0, "promo_codes_used": 0}

# Збереження історії
def save_history(history):
    with open(history_file, 'w') as file:
        json.dump(history, file)

# Збереження заблокованих користувачів
def save_banned_users(banned_users):
    with open(banned_users_file, 'w') as file:
        json.dump(banned_users, file)

# Збереження промокодів
def save_promo_codes(promo_codes):
    with open(promo_codes_file, 'w') as file:
        json.dump(promo_codes, file)

# Збереження статистики
def save_statistics(statistics):
    with open(statistics_file, 'w') as file:
        json.dump(statistics, file)

# Додавання запиту в історію
def add_to_history(user_id, text):
    banned_users = load_banned_users()
    if user_id in banned_users:
        return "You are banned and cannot interact with this bot."

    history = load_history()
    if user_id not in history:
        history[user_id] = {"requests": [], "daily_limit": 0, "last_reset": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    # Перевірка ліміту
    last_reset = datetime.strptime(history[user_id]["last_reset"], "%Y-%m-%d %H:%M:%S")
    if datetime.now() - last_reset >= timedelta(days=1):
        history[user_id]["daily_limit"] = 0
        history[user_id]["last_reset"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Перевірка на ліміт запитів
    if history[user_id]["daily_limit"] >= 100:
        return "You have reached your daily limit of 100 requests. Please try again tomorrow."

    # Додаємо запит
    history[user_id]["requests"].append({"text": text, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    history[user_id]["daily_limit"] += 1
    save_history(history)
    return None  # Повертає None, якщо ліміт не досягнуто

# Короткі і правильні відповіді для контрольних
@bot.message_handler(commands=['kontrolna_tip'])
def kontrolna_tip(message):
    subject = message.text.split(' ', 1)[1].lower() if len(message.text.split()) > 1 else ''
    tips = {
        'mathematics': "For math, remember to use formulas for area, volume, and algebraic expressions. Example: Area of a circle = pi * r^2.",
        'physics': "In physics, focus on the main laws of motion and the formulas for energy and force. Example: F = ma.",
        'chemistry': "In chemistry, remember to balance equations and understand the periodic table. Example: H2 + O2 = H2O.",
        'history': "For history, focus on key events like the World Wars, revolutions, and major discoveries.",
        'biology': "For biology, understand cellular processes and the classification of life forms."
    }
    
    if subject in tips:
        bot.reply_to(message, tips[subject])
    else:
        bot.reply_to(message, "Please provide a valid subject. Example: /kontrolna_tip mathematics")

# Генерація текстів про шаурму
def generate_shawarma_text():
    texts = [
        "Shawarma is life! Every bite is like a party in my mouth!",
        "Did you know? Shawarma is the secret to happiness! 🌯",
        "If I could, I would eat Shawarma every day!",
        "Shawarma is my soulmate. Just like me, it’s rolled up and filled with flavor!",
        "Who needs love when you have Shawarma? 😋"
    ]
    return random.choice(texts)

# Генерація аудіофайлів (звуки шаурми)
def generate_shawarma_sound():
    sound = AudioSegment.from_file("shawarma_sound.mp3")  # Замість цього використовуйте ваш власний звуковий файл
    audio_file = BytesIO()
    sound.export(audio_file, format="mp3")
    audio_file.seek(0)
    return audio_file

# Генерація фото (кружечок з текстом)
def generate_circle_image(text):
    img = Image.new('RGB', (200, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    d.text((10, 80), text, fill=(0, 0, 0), font=font)
    bio_image = BytesIO()
    img.save(bio_image, format='PNG')
    bio_image.seek(0)
    return bio_image

# Розпізнавання тексту з фото (OCR)
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_info = bot.get_file(message.photo[-1].file_id)
    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
    
    response = requests.get(file_url)
    img = Image.open(BytesIO(response.content))
    
    # Використання pytesseract для розпізнавання тексту
    text = pytesseract.image_to_string(img)
    
    if text:
        bot.reply_to(message, f"Розпізнаний текст: {text}")
    else:
        bot.reply_to(message, "Не вдалося розпізнати текст на фото.")

# Парсинг сайтів з ГДЗ (наприклад, з сайту https://www.gdz.ru/)
def parse_gdz(query):
    url = f"https://www.gdz.ru/search/?searchword={query.replace(' ', '+')}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    results = soup.find_all('div', class_='search-result')

    gdz_links = []
    for result in results:
        link = result.find('a', href=True)
        if link:
            gdz_links.append(f"https://www.gdz.ru{link['href']}")
    
    return gdz_links

# Команда для пошуку готових домашніх завдань
@bot.message_handler(commands=['gdz_search'])
def gdz_search(message):
    query = " ".join(message.text.split()[1:])
    if query:
        links = parse_gdz(query)
        if links:
            bot.reply_to(message, "\n".join(links))
        else:
            bot.reply_to(message, "No Gdz results found.")
    else:
        bot.reply_to(message, "Please provide a query to search for Gdz.")

# Автоматичний пошук відповідей у Google
@bot.message_handler(commands=['search_answer'])
def search_answer(message):
    query = " ".join(message.text.split()[1:])
    if query:
        results = search(query, num_results=3)
        bot.reply_to(message, "\n".join(results))
    else:
        bot.reply_to(message, "Please provide a search query.")

# Команда для генерації тексту про шаурму
@bot.message_handler(commands=['shawarma_joke'])
def shawarma_joke(message):
    joke = generate_shawarma_text()
    bot.reply_to(message, joke)

# Команда для генерації аудіофайлу (звуки шаурми)
@bot.message_handler(commands=['shawarma_sound'])
def shawarma_sound(message):
    audio_file = generate_shawarma_sound()
    bot.send_audio(message.chat.id, audio_file)

# Команда для генерації кружечка з текстом
@bot.message_handler(commands=['generate_circle'])
def generate_circle(message):
    text = message.text.split(' ', 1)[1] if len(message.text.split()) > 1 else 'Shawarma'
    bio_image = generate_circle_image(text)
    bot.send_photo(message.chat.id, bio_image)

# Запуск бота
bot.polling(none_stop=True)