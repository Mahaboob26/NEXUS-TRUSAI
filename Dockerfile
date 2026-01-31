FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Setup Supervisor
COPY scripts/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose Streamlit port
EXPOSE 8501

# Start supervisor
CMD ["/usr/bin/supervisord"]
