FROM python:3.13-slim

WORKDIR /app

# Install system deps (freetype for PyMuPDF, gfortran for pdf2docx)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY backend/app ./app

# Non‑root user (optional – uncomment if desired)
# USER app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]