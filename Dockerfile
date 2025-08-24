# Используем Python 3.10, чтобы PTB v20 работал корректно
FROM python:3.10-slim

WORKDIR /app

# Копируем зависимости и ставим их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем бота
COPY . .

# Запуск бота
CMD ["python", "bot.py"]
