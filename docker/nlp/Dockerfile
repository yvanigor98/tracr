FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip --no-cache-dir

# Step 1: PyTorch CPU
RUN pip install --no-cache-dir \
    torch==2.2.2 \
    --index-url https://download.pytorch.org/whl/cpu

# Step 2: BentoML + spaCy + transformers + structlog
RUN pip install --no-cache-dir \
    bentoml==1.4.36 \
    spacy==3.7.4 \
    spacy-transformers==1.3.5 \
    structlog>=24.0.0

# Step 3: en_core_web_trf wheel
RUN pip install --no-cache-dir \
    https://github.com/explosion/spacy-models/releases/download/en_core_web_trf-3.7.3/en_core_web_trf-3.7.3-py3-none-any.whl

# Copy serving module
COPY tracr/serving/ ./tracr/serving/
COPY tracr/processing/ner.py ./tracr/processing/ner.py
COPY tracr/processing/__init__.py ./tracr/processing/__init__.py
COPY tracr/config.py ./tracr/config.py
COPY tracr/__init__.py ./tracr/__init__.py

ENV PYTHONPATH=/app

EXPOSE 3000

CMD ["python", "-m", "bentoml", "serve", "tracr.serving.nlp_service:svc", "--host", "0.0.0.0", "--port", "3000"]
