# SportsBetLang API Docker Container
FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements-api.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy application
COPY lib/ ./lib/
COPY api.py .

# Expose port
EXPOSE 8000

# Run API server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
