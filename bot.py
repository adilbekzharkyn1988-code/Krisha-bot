import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот 🚀")

def main():
    app = Application.builder().token(TOKEN).build()

    # Добавляем команду /start
    app.add_handler(CommandHandler("start", start))

    # Запуск бота через polling (для локального теста)
    app.run_polling()

if __name__ == "__main__":
    main()
