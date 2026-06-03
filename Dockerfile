FROM python:3.10-slim

# Install ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render dynamically sets PORT, so we use it.
# If not set, defaults to 8081
CMD gunicorn -b 0.0.0.0:${PORT:-8081} app:app
