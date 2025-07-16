FROM python:3.9-slim

# Instala dependências do sistema para PostgreSQL (libpq-dev) e para compilação (gcc)
# E as dependências da aplicação (libreoffice, etc.)
RUN apt-get update && apt-get install -y \
    libreoffice \
    poppler-utils \
    libpq-dev \
    gcc \
    --no-install-recommends \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]