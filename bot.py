import os
import threading
from flask import Flask
from telebot import TeleBot, types

# Конфігурація
BOT_TOKEN = 7738138408:AAEMrBTn7b-G4I483n_f2b7ceKhl2eSRkdQ "  # Замініть на реальний токен
ADMIN_ID = 1119767022  # Ваш Telegram ID

# Ініціалізація
bot = TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Веб-інтерфейс для Render
@app.route('/')
def home():
    return "🤖 Бот успішно працює!", 200

# Telegram бот
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Бот активний! /help - довідка")

def run_bot():
    bot.infinity_polling()

def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

if __name__ == '__main__':
    # Запускаємо бота в окремому потоці
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Запускаємо веб-сервер у головному потоці
    run_web()