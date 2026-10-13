FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    && rm -rf /var/lib/apt/lists/*

# Limita o Tesseract a 1 thread.
# Isso reduz bastante o consumo de memória no Render.
ENV OMP_THREAD_LIMIT=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "1", "--timeout", "180"]