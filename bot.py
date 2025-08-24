from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

import os

# --- Функция для создания PDF ---
def create_pdf(filename, description, images):
    doc = SimpleDocTemplate(filename, pagesize=A4)

    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(
        "Normal",
        parent=styles["Normal"],
        fontName="Times-Roman",  # встроенный Times
        fontSize=12,
        leading=14,
    )

    elements = []

    # Описание
    elements.append(Paragraph(description, normal_style))
    elements.append(Spacer(1, 12))

    # Фото в одну строку
    img_list = []
    for img_path in images:
        img = Image(img_path, width=150, height=150)
        img_list.append(img)

    table = Table([img_list], hAlign="LEFT")
    table.setStyle(
        TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
        ])
    )

    elements.append(table)
    doc.build(elements)


# --- Telegram bot handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне текст и фото, и я соберу PDF.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text
    photos = context.user_data.get("photos", [])

    if description and photos:
        filename = "output.pdf"
        create_pdf(filename, description, photos)
        await update.message.reply_document(document=open(filename, "rb"))
        context.user_data["photos"] = []  # очищаем фото после сборки
    else:
        await update.message.reply_text("Сначала отправь фото, потом текст.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    file_path = f"{photo_file.file_id}.jpg"
    await photo_file.download_to_drive(file_path)

    photos = context.user_data.get("photos", [])
    photos.append(file_path)
    context.user_data["photos"] = photos

    await update.message.reply_text("Фото сохранено. Теперь отправь описание.")

# --- Main ---
def main():
    TOKEN = os.getenv("BOT_TOKEN")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()

if __name__ == "__main__":
    main()
