FROM python:3.13.5-slim

WORKDIR /app

# Installa solo ffmpeg e curl per healthcheck
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia i file delle dipendenze
COPY pyproject.toml uv.lock ./

# Installa uv, esporta il lock in un requirements.txt e installa con uv pip install
# --index-url specifica l'indice CPU di PyTorch per risolvere torch==2.11.0+cpu
# --extra-index-url è l'indice standard PyPI per tutte le altre dipendenze
RUN pip install --no-cache-dir uv && \
    uv export --frozen --no-hashes --no-dev --format requirements-txt > requirements.txt && \
    uv pip install --system --no-cache -r requirements.txt \
        --index-url https://download.pytorch.org/whl/cpu \
        --extra-index-url https://pypi.org/simple

# Copia il codice applicativo
COPY app.py ./
COPY src/ ./src/

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]