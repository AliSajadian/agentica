FROM python:3.11-slim-bullseye

WORKDIR /app

# install only ca-certificates for HTTPS requests
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# install dependencies first (layer caching — only rebuilds if requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# copy app code last (most frequently changing layer)
COPY . .

# non-root user for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]