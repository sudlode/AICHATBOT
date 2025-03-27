import os
import json
import random
import telebot
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment
from googlesearch import search

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
    # Створимо простий звук - ви можете додати реальні звуки шаурми, якщо маєте їх у форматі аудіо
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

# Команда для бану користувача (тільки для адміністратора)
@bot.message_handler(commands=['ban_user'])
def ban_user(message):
    if message.from_user.id == int(ADMIN_USER_ID):  # Перевірка чи це адміністратор
        user_id = int(message.text.split()[1])  # Витягнути ID користувача
        banned_users = load_banned_users()
        if user_id not in banned_users:
            banned_users.append(user_id)
            save_banned_users(banned_users)
            bot.reply_to(message, f"User {user_id} has been banned.")
        else:
            bot.reply_to(message, f"User {user_id} is already banned.")
    else:
        bot.reply_to(message, "You are not authorized to ban users.")

# Команда для створення промокодів
@bot.message_handler(commands=['promo_create'])
def promo_create(message):
    if message.from_user.id == int(ADMIN_USER_ID):  # Перевірка чи це адміністратор
        promo_code = message.text.split()[1]  # Витягнути промокод
        promo_codes = load_promo_codes()
        if promo_code not in promo_codes:
            promo_codes.append(promo_code)
            save_promo_codes(promo_codes)
            bot.reply_to(message, f"Promo code '{promo_code}' has been created.")
        else:
            bot.reply_to(message, f"Promo code '{promo_code}' already exists.")
    else:
        bot.reply_to(message, "You are not authorized to create promo codes.")

# Команда для перегляду статистики
@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id == int(ADMIN_USER_ID):  # Перевірка чи це адміністратор
        statistics = load_statistics()
        stats_message = f"Requests: {statistics['requests']}\nBans: {statistics['bans']}\nPromo Codes Used: {statistics['promo_codes_used']}"
        bot.reply_to(message, stats_message)
    else:
        bot.reply_to(message, "You are not authorized to view statistics.")

# Команда для генерації тексту про шаурму
@bot.message_handler(commands=['shawarma'])
def shawarma(message):
    response = add_to_history(message.from_user.id, "/shawarma")
    if response:
        bot.reply_to(message, response)
    else:
        text = generate_shawarma_text()
        bot.reply_to(message, text)

# Команда для генерації звуків шаурми
@bot.message_handler(commands=['shawarma_sound'])
def shawarma_sound(message):
    response = add_to_history(message.from_user.id, "/shawarma_sound")
    if response:
        bot.reply_to(message, response)
    else:
        audio = generate_shawarma_sound()
        bot.send_audio(message.chat.id, audio)

# Команда для генерації кружечка з текстом
@bot.message_handler(commands=['circle_image'])
def circle_image(message):
    text = "Shawarma!"
    response = add_to_history(message.from_user.id, "/circle_image")
    if response:
        bot.reply_to(message, response)
    else:
        image = generate_circle_image(text)
        bot.send_photo(message.chat.id, image)

# Команда для пошуку в Google
@bot.message_handler(commands=['google'])
def google_search(message):
    query = " ".join(message.text.split()[1:])
    if query:
        results = search(query, num_results=5)
        bot.reply_to(message, "\n".join(results))
    else:
        bot.reply_to(message, "Please provide a search query.")

# Команда для ГДЗ
@bot.message_handler(commands=['gdz'])
def gdz(message):
    bot.reply_to(message, "Here are some Gdz sites:\n- https://www.gdz.ru\n- https://gdz.com")

# Запуск бота
bot.polling(none_stop=True)