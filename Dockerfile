FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p static uploads results temp

# Copy index.html to static directory if it exists
RUN if [ -f "index.html" ] && [ ! -f "static/index.html" ]; then \
    mkdir -p static && \
    cp index.html static/index.html; \
    fi

# Create empty .env file if it doesn't exist
RUN if [ ! -f ".env" ]; then \
    echo "# API Keys\nOPENAI_API_KEY=\nGOOGLE_KEY=\nMINERU_API_KEY=\n\n# Model Settings\nCRAWLER_MODEL=deepseek-chat\nSELECTOR_MODEL=deepseek-chat\nREVIEW_MODEL=qwen-max-2025-01-25" > .env; \
    fi

# Create empty api.txt file for MinerU if it doesn't exist
RUN if [ ! -f "api.txt" ]; then \
    touch api.txt; \
    fi

# Expose the port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
