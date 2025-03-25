import logging
from telebot import TeleBot, types

# Налаштування
BOT_TOKEN = "7738138408:AAEMrBTn7b-G4I483n_f2b7ceKhl2eSRkdQ"  # Отримайте у @BotFather
ADMIN_ID = 1119767022  # Ваш Telegram ID (дізнайтесь у @userinfobot)

# Ініціалізація
bot = TeleBot(BOT_TOKEN)
logging.basicConfig(level=logging.INFO)

# Перевірка адміна
def is_admin(user_id):
    return user_id == ADMIN_ID

# Головне меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("ℹ️ Допомога"))
    if is_admin(bot.message.chat.id):
        markup.add(types.KeyboardButton("👨‍💻 Адмінка"))
    return markup

# Обробник /start
@bot.message_handler(commands=['start'])
def start(message):
    try:
        bot.send_message(
            message.chat.id,
            "🔹 Бот успішно запущений!\n\n"
            "Доступні команди:\n"
            "/help - Довідка\n"
            "/admin - Панель керування",
            reply_markup=main_menu()
        )
    except Exception as e:
        logging.error(f"Помилка: {e}")

# Адмін-панель
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⛔ Доступ заборонено!")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Статистика", "📢 Розсилка")
    markup.add("🔙 Назад")
    
    bot.send_message(
        message.chat.id,
        "👨‍💻 Адмін-панель:",
        reply_markup=markup
    )

# Обробник кнопки "Статистика"
@bot.message_handler(func=lambda m: m.text == "📊 Статистика" and is_admin(m.from_user.id))
def show_stats(message):
    bot.send_message(
        message.chat.id,
        "📊 Статистика:\n\n"
        "Користувачів: 100\n"
        "Активних сьогодні: 42\n"
        "Забанених: 3"
    )

# Запуск бота
if __name__ == '__main__':
    logging.info("Бот запускається...")
    bot.infinity_polling()