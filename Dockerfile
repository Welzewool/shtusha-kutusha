FROM python:3.11-alpine

# Временная зона
RUN apk add --no-cache tzdata
ENV TZ=Europe/Moscow

WORKDIR /app

# Устанавливаем PYTHONPATH
ENV PYTHONPATH=/app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

CMD ["python", "-u", "bot/main.py"]