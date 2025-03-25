import os
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from flask import Flask, request

# Конфігурація
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = "https://your-render-app.onrender.com/webhook"
ADMINS = [1119767022]  # Ваш Telegram ID

# Ініціалізація
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Клавіатура
def main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("ℹ️ Допомога"))
    markup.add(KeyboardButton("🎤 Голосове"))
    return markup

# Команди
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "🚀 Бот запущений!", reply_markup=main_keyboard())

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id not in ADMINS:
        return
    bot.send_message(message.chat.id, "👨‍💻 Адмін-панель:", reply_markup=admin_keyboard())

# Обробник текстових повідомлень
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text == "ℹ️ Допомога":
        bot.send_message(message.chat.id, "Список команд:\n/start - Перезапуск\n/admin - Адмінка")
    elif message.text == "🎤 Голосове":
        bot.send_message(message.chat.id, "Напишіть текст для перетворення у голос (напр. 'голос Привіт')")

# Вебхук для Render
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        return 'Bad request', 400

# Запуск
if __name__ == '__main__':
    if os.getenv("ENV") == "production":
        bot.remove_webhook()
        bot.set_webhook(url=WEBHOOK_URL)
        app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
    else:
        bot.polling(none_stop=True)
