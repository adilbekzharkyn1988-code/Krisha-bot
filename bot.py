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
        "Привет! Я бот 🚀\nИспользуй команду:\n/pdf <ссылка на объявление>\nчтобы получить красиво оформленный PDF."
    )

class PDF(FPDF):
    def add_image_row(self, img_paths, max_width=180, spacing=5):
        # Вставляет несколько изображений в ряд
        x_start = self.get_x()
        y_start = self.get_y()
        max_height = 0
        for img_path in img_paths:
            try:
                w, h = Image.open(img_path).size
                ratio = max_width / len(img_paths) / w
                w_new = w * ratio
                h_new = h * ratio
                if self.get_x() + w_new > 190:  # Перенос на следующую строку
                    self.ln(max_height + spacing)
                    self.set_x(x_start)
                    max_height = 0
                self.image(img_path, x=self.get_x(), y=self.get_y(), w=w_new)
                self.set_x(self.get_x() + w_new + spacing)
                max_height = max(max_height, h_new)
            except:
                continue
        self.ln(max_height + spacing)

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

        # Все фотографии
        img_tags = soup.select("img.gallery__image")
        img_urls = [img.get("src") for img in img_tags if img.get("src")]
        img_paths = []

        for i, img_url in enumerate(img_urls):
            try:
                img_response = requests.get(img_url)
                image = Image.open(BytesIO(img_response.content))
                img_path = f"temp_{i}.jpg"
                image.save(img_path)
                img_paths.append(img_path)
            except:
                continue

        # Создаём PDF
        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Заголовок
        pdf.set_font("Arial", "B", 16)
        pdf.multi_cell(0, 10, title, align="C")
        pdf.ln(5)

        # Цена
        pdf.set_font("Arial", "B", 14)
        pdf.multi_cell(0, 8, price)
        pdf.ln(3)

        # Описание
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 6, description)
        pdf.ln(5)

        # Фото
        if img_paths:
            pdf.add_image_row(img_paths)
            for path in img_paths:
                os.remove(path)

        # Ссылка
        pdf.ln(5)
        pdf.set_font("Arial", "I", 10)
        pdf.multi_cell(0, 6, f"Ссылка на объявление: {ad_url}")

        pdf_path = "krisha_ad.pdf"
        pdf.output(pdf_path)

        # Отправляем PDF
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
