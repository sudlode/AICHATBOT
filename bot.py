import os
import logging
from telebot import TeleBot, types
from telebot.util import quick_markup
from dotenv import load_dotenv

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Завантаження конфігурації
load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMINS = [1119767022]  # Ваш Telegram ID

# Перевірка токена
if not Config.BOT_TOKEN:
    logger.error("Не вказано BOT_TOKEN у змінних середовища!")
    exit(1)

# Ініціалізація бота
bot = TeleBot(Config.BOT_TOKEN)

# Клавіатури
def main_menu():
    return quick_markup({
        'ℹ️ Допомога': {'callback_data': 'help'},
        '🎤 Голосове': {'callback_data': 'voice'},
        '👨‍💻 Адмінка': {'callback_data': 'admin'}
    }, row_width=2)

# Обробники подій
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        bot.reply_to(
            message,
            "🌟 Вітаю! Я ваш бот-помічник.",
            reply_markup=main_menu()
        )
        logger.info(f"Новий користувач: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Помилка в /start: {e}")

@bot.callback_query_handler(func=lambda call: True)
def handle_buttons(call):
    try:
        if call.data == 'help':
            bot.send_message(
                call.message.chat.id,
                "📚 Доступні команди:\n"
                "/start - Головне меню\n"
                "/voice - Голосові повідомлення"
            )
        elif call.data == 'voice':
            msg = bot.send_message(
                call.message.chat.id,
                "Напишіть текст для перетворення у голос:"
            )
            bot.register_next_step_handler(msg, process_voice)
        elif call.data == 'admin':
            if call.from_user.id in Config.ADMINS:
                show_admin_panel(call.message)
            else:
                bot.answer_callback_query(call.id, "⛔ Доступ заборонено!")
    except Exception as e:
        logger.error(f"Помилка обробки кнопки: {e}")

def process_voice(message):
    try:
        text = message.text.strip()
        if not text:
            bot.reply_to(message, "❌ Ви не ввели текст!")
            return
            
        # Тут буде логіка генерації голосу
        bot.reply_to(message, f"🔊 Ваш текст: {text}")
    except Exception as e:
        logger.error(f"Помилка обробки голосу: {e}")

def show_admin_panel(message):
    try:
        bot.send_message(
            message.chat.id,
            "👨‍💻 Адмін-панель:",
            reply_markup=quick_markup({
                '📊 Статистика': {'callback_data': 'stats'},
                '📢 Розсилка': {'callback_data': 'broadcast'}
            })
        )
    except Exception as e:
        logger.error(f"Помилка адмін-панелі: {e}")

# Запуск бота
if __name__ == '__main__':
    logger.info("Бот запускається...")
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.critical(f"Збій у роботі бота: {e}")
