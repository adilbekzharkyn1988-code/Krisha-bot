import os
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
from PIL import Image
from io import BytesIO
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот 🚀\nИспользуй команду:\n/pdf <ссылка на объявление>\nчтобы получить PDF с кириллицей."
    )

async def create_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи ссылку на объявление: /pdf <ссылка>")
        return

    ad_url = context.args[0]
    await update.message.reply_text(f"Создаю PDF для {ad_url}... ⏳")

    try:
        response = requests.get(ad_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")

        # Название
        title_tag = soup.select_one("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Название отсутствует"

        # Цена
        price_tag = soup.select_one("div.offer__price")
        price = price_tag.get_text(strip=True) if price_tag else "Цена не указана"

        # Описание
        desc_tag = soup.select_one("div.offer__description")
        description = desc_tag.get_text(strip=True) if desc_tag else "Описание отсутствует"

        # Фото
        img_tag = soup.select_one("img.gallery__image")
        img_url = img_tag.get("src") if img_tag else None

        # Создаём PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)  # подключаем шрифт
        pdf.set_font('DejaVu', 'B', 16)
        pdf.multi_cell(0, 10, title, align="C")
        pdf.ln(5)

        pdf.set_font('DejaVu', '', 12)
        pdf.multi_cell(0, 8, f"{price}\n\n{description}\n\nСсылка: {ad_url}")
        pdf.ln(5)

        if img_url:
            try:
                img_response = requests.get(img_url)
                image = Image.open(BytesIO(img_response.content))
                img_path = "temp.jpg"
                image.save(img_path)
                pdf.image(img_path, w=150)
                os.remove(img_path)
                pdf.ln(5)
            except:
                pass

        pdf_path = "krisha_ad.pdf"
        pdf.output(pdf_path)

        with open(pdf_path, "rb") as f:
            await update.message.reply_document(f)

    except Exception as e:
        await update.message.reply_text(f"Ошибка при парсинге: {e}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pdf", create_pdf))
    app.run_polling()

if __name__ == "__main__":
    main()
