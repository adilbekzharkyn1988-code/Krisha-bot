import os
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
from PIL import Image
from io import BytesIO
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")  # Токен из Render

# === Создание PDF ===
def create_pdf(data, filename="output.pdf"):
    pdf = FPDF()
    pdf.add_page()

    # Подключаем шрифт (файл DejaVuSans.ttf положи в корень проекта!)
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", "", 16)

    # Заголовок
    pdf.multi_cell(0, 10, data["title"], align="C")
    pdf.ln(5)

    # Цена
    pdf.set_font("DejaVu", "", 14)
    pdf.set_text_color(200, 0, 0)
    pdf.multi_cell(0, 10, f"Цена: {data['price']}", align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # Параметры
    pdf.set_font("DejaVu", "", 12)
    pdf.multi_cell(0, 10, "Параметры:", align="L")
    pdf.ln(2)
    for key, value in data["params"].items():
        pdf.multi_cell(0, 8, f"• {key}: {value}")
    pdf.ln(5)

    # Описание
    if data["description"]:
        pdf.set_font("DejaVu", "", 12)
        pdf.multi_cell(0, 10, "Описание:", align="L")
        pdf.ln(2)
        for para in data["description"]:
            pdf.multi_cell(0, 8, para)
            pdf.ln(3)

    # Фото (макс 6)
    if data["images"]:
        pdf.add_page()
        pdf.set_font("DejaVu", "", 14)
        pdf.multi_cell(0, 10, "Фотографии", align="C")
        pdf.ln(5)

        for i, img_url in enumerate(data["images"][:6]):
            try:
                img_response = requests.get(img_url, timeout=10)
                image = Image.open(BytesIO(img_response.content))
                img_path = f"temp_{i}.jpg"
                image.save(img_path)

                pdf.image(img_path, w=170)  # подгоняем по ширине страницы
                os.remove(img_path)
                pdf.ln(5)
            except Exception as e:
                print("Ошибка загрузки фото:", e)

    # Ссылка
    pdf.set_font("DejaVu", "", 10)
    pdf.ln(10)
    pdf.multi_cell(0, 8, f"Ссылка: {data['url']}")

    pdf.output(filename)


# === Парсинг Krisha ===
def parse_krisha(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    r.encoding = "utf-8"
    soup = BeautifulSoup(r.text, "html.parser")

    # Заголовок и цена
    title = soup.select_one("h1").get_text(strip=True) if soup.select_one("h1") else "Без заголовка"
    price = soup.select_one("div.offer__price").get_text(strip=True) if soup.select_one("div.offer__price") else "Без цены"

    # Параметры (этаж, площадь и т.п.)
    params = {}
    for row in soup.select("div.offer__parameters div.offer__parameters-item"):
        key = row.select_one("span").get_text(strip=True) if row.select_one("span") else ""
        value = row.get_text(strip=True).replace(key, "").strip()
        if key and value:
            params[key] = value

    # Описание
    desc_paragraphs = []
    desc_container = soup.select_one("div.offer__description")
    if desc_container:
        for p in desc_container.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                desc_paragraphs.append(text)

    # Фотографии
    images = []
    for img in soup.select("img[data-src]"):
        src = img.get("data-src")
        if src and "krisha" in src:
            images.append(src)

    return {
        "title": title,
        "price": price,
        "params": params,
        "description": desc_paragraphs,
        "images": images,
        "url": url
    }


# === Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет 👋 Пришли мне ссылку на объявление Krisha.kz, и я сделаю PDF-презентацию.")

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

    # Запуск через webhook (Render)
    port = int(os.environ.get("PORT", 8443))
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,
        webhook_url=f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{TOKEN}"
    )


if __name__ == "__main__":
    main()
