import os
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
from PIL import Image
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")  # токен бота из Render

# === Создание PDF ===
def create_pdf(data, filename="output.pdf"):
    pdf = FPDF()
    pdf.add_page()

    # Шрифты (utf-8, кириллица)
    pdf.add_font("DejaVu", "", fname="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", "", 14)

    # Заголовок
    pdf.multi_cell(0, 10, data["title"], align="L")
    pdf.ln(5)

    # Цена
    pdf.set_font("DejaVu", "", 12)
    pdf.multi_cell(0, 10, f"Цена: {data['price']}")
    pdf.ln(5)

    # Описание (абзацы)
    for para in data["description"]:
        pdf.multi_cell(0, 8, para)
        pdf.ln(3)

    # Фотографии (макс 5 шт)
    for img_url in data["images"][:5]:
        try:
            img_response = requests.get(img_url, timeout=10)
            image = Image.open(BytesIO(img_response.content))
            img_path = "temp.jpg"
            image.save(img_path)
            pdf.image(img_path, w=150)
            os.remove(img_path)
            pdf.ln(5)
        except Exception as e:
            print("Ошибка загрузки фото:", e)

    # Ссылка
    pdf.set_font("DejaVu", "", 10)
    pdf.ln(5)
    pdf.multi_cell(0, 8, f"Ссылка: {data['url']}")

    pdf.output(filename)


# === Парсинг Krisha ===
def parse_krisha(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "html.parser")

    title = soup.select_one("h1").get_text(strip=True) if soup.select_one("h1") else "Без заголовка"
    price = soup.select_one("div.offer__price").get_text(strip=True) if soup.select_one("div.offer__price") else "Без цены"

    # Описание (берём <p>)
    desc_paragraphs = []
    desc_container = soup.select_one("div.offer__description")
    if desc_container:
        for p in desc_container.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                desc_paragraphs.append(text)
    if not desc_paragraphs and desc_container:
        desc_paragraphs = desc_container.get_text(strip=True).split("\n")

    # Фото
    images = []
    for img in soup.select("img.gallery__image"):
        src = img.get("src")
        if src:
            images.append(src)

    return {
        "title": title,
        "price": price,
        "description": desc_paragraphs,
        "images": images,
        "url": url
    }


# === Telegram handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет 👋 Пришли мне ссылку на объявление Krisha.kz, и я сделаю PDF.")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "krisha.kz" not in url:
        await update.message.reply_text("Отправь ссылку на объявление Krisha.kz")
        return

    try:
        await update.message.reply_text("Парсю объявление, подожди 5–10 секунд...")
        data = parse_krisha(url)
        create_pdf(data, "result.pdf")
        await update.message.reply_document(document=open("result.pdf", "rb"))
    except Exception as e:
        await update.message.reply_text(f"Ошибка при парсинге: {e}")


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()


if __name__ == "__main__":
    main()
