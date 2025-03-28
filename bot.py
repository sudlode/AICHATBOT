import os
import json
import random
import telebot
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment
from googlesearch import search
from dotenv import load_dotenv  # Add this line to import load_dotenv

# Load environment variables from .env file
load_dotenv()  # Add this line to load the environment variables

# API keys
TOKEN = os.getenv("TOKEN")  # Your token for the Telegram bot
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Your key for OpenAI

# Initialize the bot
bot = telebot.TeleBot(TOKEN)

# Initialize your Telegram ID for activating the administrator
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")  # Your ID for the administrator

# Path to files for saving history, banned users, and promo codes
history_file = "history.json"
banned_users_file = "banned_users.json"
promo_codes_file = "promo_codes.json"
statistics_file = "statistics.json"

# Load history
def load_history():
    if os.path.exists(history_file):
        with open(history_file, 'r') as file:
            return json.load(file)
    return {}

# Load banned users
def load_banned_users():
    if os.path.exists(banned_users_file):
        with open(banned_users_file, 'r') as file:
            return json.load(file)
    return []

# Load promo codes
def load_promo_codes():
    if os.path.exists(promo_codes_file):
        with open(promo_codes_file, 'r') as file:
            return json.load(file)
    return {}

# Load statistics
def load_statistics():
    if os.path.exists(statistics_file):
        with open(statistics_file, 'r') as file:
            return json.load(file)
    return {"requests": 0, "bans": 0, "promo_codes_used": 0}

# Save history
def save_history(history):
    with open(history_file, 'w') as file:
        json.dump(history, file)

# Save banned users
def save_banned_users(banned_users):
    with open(banned_users_file, 'w') as file:
        json.dump(banned_users, file)

# Save promo codes
def save_promo_codes(promo_codes):
    with open(promo_codes_file, 'w') as file:
        json.dump(promo_codes, file)

# Save statistics
def save_statistics(statistics):
    with open(statistics_file, 'w') as file:
        json.dump(statistics, file)

# Add request to history
def add_to_history(user_id, text):
    banned_users = load_banned_users()
    if user_id in banned_users:
        return "You are banned and cannot interact with this bot."

    history = load_history()
    if user_id not in history:
        history[user_id] = {"requests": [], "daily_limit": 0, "last_reset": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    
    # Check limit
    last_reset = datetime.strptime(history[user_id]["last_reset"], "%Y-%m-%d %H:%M:%S")
    if datetime.now() - last_reset >= timedelta(days=1):
        history[user_id]["daily_limit"] = 0
        history[user_id]["last_reset"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check request limit
    if history[user_id]["daily_limit"] >= 100:
        return "You have reached your daily limit of 100 requests. Please try again tomorrow."

    # Add request
    history[user_id]["requests"].append({"text": text, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    history[user_id]["daily_limit"] += 1
    save_history(history)
    return None  # Returns None if limit is not reached

# Generate shawarma text
def generate_shawarma_text():
    texts = [
        "Shawarma is life! Every bite is like a party in my mouth!",
        "Did you know? Shawarma is the secret to happiness! 🌯",
        "If I could, I would eat Shawarma every day!",
        "Shawarma is my soulmate. Just like me, it’s rolled up and filled with flavor!",
        "Who needs love when you have Shawarma? 😋"
    ]
    return random.choice(texts)

# Generate shawarma sound
def generate_shawarma_sound():
    # Create a simple sound - you can add real shawarma sounds if you have them in audio format
    sound = AudioSegment.from_file("shawarma_sound.mp3")  # Use your own sound file instead
    audio_file = BytesIO()
    sound.export(audio_file, format="mp3")
    audio_file.seek(0)
    return audio_file

# Generate circle image
def generate_circle_image(text):
    img = Image.new('RGB', (200, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    d.text((10, 80), text, fill=(0, 0, 0), font=font)
    bio_image = BytesIO()
    img.save(bio_image, format='PNG')
    bio_image.seek(0)
    return bio_image

# Command to ban user (admin only)
@bot.message_handler(commands=['ban_user'])
def ban_user(message):
    if message.from_user.id == int(ADMIN_USER_ID):  # Check if admin
        user_id = int(message.text.split()[1])  # Extract user ID
        banned_users = load_banned_users()
        if user_id not in banned_users:
            banned_users.append(user_id)
            save_banned_users(banned_users)
            bot.reply_to(message, f"User {user_id} has been banned.")
        else:
            bot.reply_to(message, f"User {user_id} is already banned.")
    else:
        bot.reply_to(message, "You are not authorized to ban users.")

# Command to create promo codes (admin only)
@bot.message_handler(commands=['promo_create'])
def promo_create(message):
    if message.from_user.id == int(ADMIN_USER_ID):  # Check if admin
        promo_code = message.text.split()[1]  # Extract promo code
        promo_codes = load_promo_codes()
        if promo_code not in promo_codes:
            promo_codes.append(promo_code)
            save_promo_codes(promo_codes)
            bot.reply_to(message, f"Promo code '{promo_code}' has been created.")
        else:
            bot.reply_to(message, f"Promo code '{promo_code}' already exists.")
    else:
        bot.reply_to(message, "You are not authorized to create promo codes.")

# Command to view statistics (admin only)
@bot.message_handler(commands=['stats'])
def stats(message):
    if message.from_user.id == int(ADMIN_USER_ID):  # Check if admin
        statistics = load_statistics()
        stats_message = f"Requests: {statistics['requests']}\nBans: {statistics['bans']}\nPromo Codes Used: {statistics['promo_codes_used']}"
        bot.reply_to(message, stats_message)
    else:
        bot.reply_to(message, "You are not authorized to view statistics.")

# Command to generate shawarma text
@bot.message_handler(commands=['shawarma'])
def shawarma(message):
    response = add_to_history(message.from_user.id, "/shawarma")
    if response:
        bot.reply_to(message, response)
    else:
        text = generate_shawarma_text()
        bot.reply_to(message, text)

# Command to generate shawarma sounds
@bot.message_handler(commands=['shawarma_sound'])
def shawarma_sound(message):
    response = add_to_history(message.from_user.id, "/shawarma_sound")
    if response:
        bot.reply_to(message, response)
    else:
        audio = generate_shawarma_sound()
        bot.send_audio(message.chat.id, audio)

# Command to generate circle image with text
@bot.message_handler(commands=['circle_image'])
def circle_image(message):
    text = "Shawarma!"
    response = add_to_history(message.from_user.id, "/circle_image")
    if response:
        bot.reply_to(message, response)
    else:
        image = generate_circle_image(text)
        bot.send_photo(message.chat.id, image)

# Command for Google search
@bot.message_handler(commands=['google'])
def google_search(message):
    query = " ".join(message.text.split()[1:])
    if query:
        results = search(query, num_results=5)
        bot.reply_to(message, "\n".join(results))
    else:
        bot.reply_to(message, "Please provide a search query.")

# Command for GDZ
@bot.message_handler(commands=['gdz'])
def gdz(message):
    bot.reply_to(message, "Here are some Gdz sites:\n- https://www.gdz.ru/\n- https://gdz-online.com/")

# Command to view user history
@bot.message_handler(commands=['history'])
def history(message):
    user_id = message.from_user.id
    history_data = load_history()
    bot.reply_to(message, str(history_data.get(user_id, "No history found.")))

bot.polling()
