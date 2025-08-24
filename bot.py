import os
import telegram
print("PTB version:", telegram.__version__)

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


# Получаем токен из переменной окружения
TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот 🚀")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Используй /start для начала.")

def main():
    # Создаём асинхронное приложение
    app = Application.builder().token(TOKEN).build()

    # Добавляем команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    # Запуск бота через асинхронный polling
    app.run_polling()

if __name__ == "__main__":
    main()
