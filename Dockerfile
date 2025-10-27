# --- Base Python image ---
FROM python:3.12-slim

# --- Set working directory ---
WORKDIR /app

# --- Install Playwright & Chromium dependencies ---
RUN apt-get update && apt-get install -y \
    libnss3 libatk-bridge2.0-0 libatk1.0-0 libcups2 libdbus-1-3 libdrm2 \
    libgbm1 libglib2.0-0 libgtk-3-0 libxcomposite1 libxdamage1 libxrandr2 \
    libasound2 libpangocairo-1.0-0 libpango-1.0-0 libx11-xcb1 libxcb1 \
    libxshmfence1 libxfixes3 libxrender1 libxext6 libxkbcommon0 libwayland-client0 \
    libwayland-cursor0 fonts-liberation wget curl unzip xvfb ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- Copy app code ---
COPY . .

# --- Install Python dependencies ---
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --- Install Chromium for Playwright ---
RUN playwright install chromium

# --- Expose app port ---
EXPOSE 8080

# --- Environment variable for Flask socket mode ---
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# --- Run the Flask-SocketIO server with eventlet ---
CMD ["python", "app.py"]
