FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy top-level requirements; adjust if you split requirements for backend/frontend
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend/ ./backend/

WORKDIR /app/backend

EXPOSE 8000

# Use uvicorn; adjust module path if your FastAPI app is in a different module
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]