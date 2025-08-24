# syntax=docker/dockerfile:1

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

# System deps for building wheels (bcrypt) and openpyxl fonts, locales
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Create a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Default envs
ENV FLASK_APP=raskladka.wsgi:application \
    FLASK_ENV=production \
    SECRET_KEY=change-me \
    DATABASE_URI=sqlite:////app/instance/meals.db

# Ensure instance folder exists and is writable
RUN mkdir -p /app/instance && chmod 700 /app/instance

EXPOSE 5000

# Healthcheck: use Python stdlib to avoid extra OS deps
HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD python -c "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=3).status==200 else sys.exit(1)"

# Run via gunicorn, tuned for prod (single-line exec form)
CMD ["gunicorn", "-w", "4", "--threads", "2", "--timeout", "60", "--access-logfile", "-", "--error-logfile", "-", "-b", "0.0.0.0:5000", "raskladka.wsgi:application"]


