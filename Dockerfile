FROM python:3.13.5-slim

WORKDIR /app

# Installa solo ffmpeg e curl per healthcheck
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia i file delle dipendenze
COPY pyproject.toml uv.lock ./

# Usa uv in modalità compatibilità pip per installare tutto a livello di sistema
RUN pip install --no-cache-dir uv && \
    uv pip install --system -r pyproject.toml

# Copia il codice applicativo
COPY app.py ./
COPY src/ ./src/

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]