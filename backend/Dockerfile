# Estágio 1: Build com dependências de compilação
FROM python:3.9-slim as builder

# Instala as dependências do sistema
RUN apt-get update && apt-get install -y libreoffice poppler-utils --no-install-recommends \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Instala as dependências Python
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Estágio 2: Imagem final, mais leve
FROM python:3.9-slim

# Copia as dependências do sistema do estágio anterior
COPY --from=builder /usr/lib/ /usr/lib/
COPY --from=builder /usr/share/ /usr/share/
COPY --from=builder /usr/bin/libreoffice /usr/bin/libreoffice
COPY --from=builder /usr/bin/soffice* /usr/bin/soffice*
COPY --from=builder /usr/bin/pdftoppm /usr/bin/pdftoppm

# Copia as dependências Python instaladas
WORKDIR /app
COPY --from=builder /app /app

# Copia o código da aplicação
COPY . .

# Comando para iniciar o servidor Gunicorn
# -k: tipo de worker
# -w: número de workers (ajuste conforme a CPU da sua VPS, ex: (2 * numero_de_cores) + 1)
# -b: endereço e porta
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]