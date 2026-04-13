FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy environment code
COPY env/ ./env/
COPY tasks/ ./tasks/
COPY baseline.py .
COPY inference.py .
COPY app.py .
COPY openenv.yaml .
COPY README.md .

# Create __init__ files
RUN touch env/__init__.py tasks/__init__.py scripts/__init__.py

# Expose port for HF Spaces
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
