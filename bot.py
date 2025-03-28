import os
import json
import random
import telebot
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment
from googlesearch import search
from dotenv import load_dotenv  # Додайте цей рядок для імпорту load_dotenv

# Завантажте змінні середовища з файлу .env
load_dotenv()  # Додайте цей рядок для завантаження змінних середовища

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
        return "Ви заблоковані і не можете взаємодіяти з цим ботом."

    history = load_history()
    if user_id not in history:
        history[user_id] = {"requests": [], "daily_limit": 0, "last_reset": datetime.now().strftime("%Y-%м-%d %H:%М:%S")}
    
    # Перевірка ліміту
    last_reset = datetime.strptime(history[user_id]["last_reset"], "%Y-%м-%д %H:%М:%S")
    if datetime.now() - last_reset >= timedelta(days=1):
        history[user_id]["daily_limit"] = 0
        history[user_id]["last_reset"] = datetime.now().strftime("%Y-%м-%д %H:%М:%S")
    
    # Перевірка на ліміт запитів
    if history[user_id]["daily_limit"] >= 100:
        return "Ви досягли свого денного ліміту у 100 запитів. Будь ласка, спробуйте знову завтра."

    # Додаємо запит
    history[user_id]["requests"].append({"text": text, "time": datetime.now().strftime("%Y-%м-%д %H:%М:%S")})
    history[user_id]["daily_limit"] += 1
    save_history(history)
    return None  # Повертає None, якщо ліміт не досягнуто

# Генерація текстів про шаурму
def generate_shawarma_text():
    texts = [
        "Шаурма - це життя! Кожен шматочок - це як свято у роті!",
        "Чи знаєте ви? Шаурма - це секрет щастя! 🌯",
        "Якби я міг, я б їв шаурму кожного дня!",
        "Шаурма - це моя душа. Як і я, вона згорнута і наповнена смаком!",
        "Хто потребує любові, коли є шаурма? 😋"
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
            bot.reply_to(message, f"Користувача {user_id} заблоковано.")
        else:
            bot.reply_to(message, f"Користувач {user_id} вже заблокований.")
    else:
        bot.reply_to(message, "Ви не авторизовані для блокування користувачів.")

# Команда для створення промокодів
@bot.message_handler(commands=['promo_create'])
def promo_create(message):
    if message.from_user.id == int(ADMIN_USER_ID):  # Перевірка чи це адміністратор
        promo_code = message.text.split()[1]  # Витягнути промокод
        promo_codes = load_promo_codes()
        if promo_code not in promo_codes:
            promo_codes.append(promo_code)
            save_promo_codes(promo_codes)
            bot.reply_to(message, f"Промокод '{promo_code}' створено.")
        else:
            bot.reply_to(message, f"Промокод '{promo_code}' вже існує.")
    else:
        bot.reply_to(message, "Ви не авторизовані для створення промокодів.")

# Команда для перегляду статистики
@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id == int(ADMIN_USER_ID):  # Перевірка чи це адміністратор
        statistics = load_statistics()
        stats_message = f"Запити: {statistics['requests']}\nБлокування: {statistics['bans']}\nВикористані промокоди: {statistics['promo_codes_used']}"
        bot.reply_to(message, stats_message)
    else:
        bot.reply_to(message, "Ви не авторизовані для перегляду статистики.")

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
    text = "Шаурма!"
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
        bot.reply_to(message, "Будь ласка, надайте запит для пошуку.")

# Команда для ГДЗ
@bot.message_handler(commands=['gdz'])
def gdz(message):
    bot.reply_to(message, "Ось деякі сайти з ГДЗ:\n- https://www.gdz.ru/\n- https://gdz-online.com/")

# Команда для перегляду історії користувача
@bot.message_handler(commands=['history'])
def history(message):
    user_id = message.from_user.id
    history_data = load_history()
    bot.reply_to(message, str(history_data.get(user_id, "Історія не знайдена.")))

bot.polling()
