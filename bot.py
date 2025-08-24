import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Регистрируем шрифт с кириллицей
pdfmetrics.registerFont(TTFont("TimesNewRoman", "times.ttf"))

def parse_krisha(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    price = soup.select_one(".offer__price")
    price = price.get_text(" ", strip=True) if price else "Цена не указана"

    address = soup.select_one(".offer__location")
    address = address.get_text(" ", strip=True) if address else "Адрес не указан"

    params = [li.get_text(" ", strip=True) for li in soup.select(".offer__parameters li")]
    params_text = "\n".join(params) if params else "Параметры не найдены"

    desc = soup.select_one(".offer__description")
    desc = desc.get_text(" ", strip=True) if desc else "Описание отсутствует"

    photos = []
    for img in soup.select(".gallery__image img"):
        src = img.get("src") or img.get("data-src") or ""
        if src.startswith("http"):
            photos.append(src)

    return price, address, params_text, desc, photos[:3]


def make_pdf(price, address, params, desc, photos, filename="output.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = "TimesNewRoman"

    elements = []
    elements.append(Paragraph(f"<b>{price}</b>", style))
    elements.append(Paragraph(f"📍 {address}", style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(params, style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(desc, style))
    elements.append(Spacer(1, 20))

    row = []
    for url in photos:
        try:
            img_data = requests.get(url, timeout=10).content
            img_path = f"/tmp/{os.path.basename(url)}.jpg"
            with open(img_path, "wb") as f:
                f.write(img_data)
            row.append(Image(img_path, width=150, height=100))
        except:
            pass

    if row:
        table = Table([row], spaceBefore=10, spaceAfter=10)
        elements.append(table)

    doc.build(elements)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет 👋 Пришли ссылку с krisha.kz, я сделаю PDF с описанием и фото 🏠")


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        await update.message.reply_text("Отправь корректную ссылку 🔗")
        return

    try:
        price, address, params, desc, photos = parse_krisha(url)
        make_pdf(price, address, params, desc, photos, "output.pdf")

        await update.message.reply_document(document=open("output.pdf", "rb"))

    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")


def main():
    token = os.environ["BOT_TOKEN"]
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.run_polling()


if __name__ == "__main__":
    main()
