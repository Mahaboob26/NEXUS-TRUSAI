FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend source
COPY frontend/ ./frontend/

WORKDIR /app/frontend

EXPOSE 8501

# Adjust app filename if different (e.g., streamlit_app.py)
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]