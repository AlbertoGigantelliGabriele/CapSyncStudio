FROM python:3.13.5-slim

WORKDIR /app

# Installa ffmpeg (per il video) e curl (per l'healthcheck)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia solo le dipendenze per sfruttare la cache di Docker
COPY requirements.txt ./

# Installa le librerie usando uv per la massima velocità
RUN pip install --no-cache-dir uv && \
    uv pip install --system -r requirements.txt

# Copia il resto del progetto
COPY app.py ./
COPY src/ ./src/

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]