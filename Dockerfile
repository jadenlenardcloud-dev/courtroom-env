# Courtroom Argument Simulator — OpenEnv Environment
# Compatible with Hugging Face Spaces (tagged: openenv)

FROM python:3.11-slim

LABEL name="courtroom-argument-simulator"
LABEL version="1.0.0"
LABEL description="OpenEnv Courtroom Argument Simulator"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Mandatory env vars — inject via HF Space secrets or docker -e flags
ENV HF_TOKEN=""
ENV API_BASE_URL="https://api.openai.com/v1"
ENV MODEL_NAME="gpt-4o-mini"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 7860

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
