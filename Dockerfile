FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary application directories
RUN mkdir -p /app/data /app/uploads /app/static /app/templates

# Copy all application files
COPY . .

# Set permissions for Hugging Face user (UID 1000)
RUN chmod -R 777 /app/data /app/uploads

# Expose Hugging Face default port
EXPOSE 7860

# Run the FastAPI application on 0.0.0.0:7860
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
