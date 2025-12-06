FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# ffmpeg is needed for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories for volumes
RUN mkdir -p /app/uploads /app/data /root/.cache/whisper

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
