FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface
ENV HF_HUB_DISABLE_TELEMETRY=1

RUN pip install --no-cache-dir \
    torch torchvision \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt requirements-ml.txt ./

RUN pip install --no-cache-dir -r requirements.txt -r requirements-ml.txt

RUN python -c "\
from transformers import SegformerForSemanticSegmentation, SegformerImageProcessor; \
SegformerImageProcessor.from_pretrained('mattmdjaga/segformer_b2_clothes'); \
SegformerForSemanticSegmentation.from_pretrained('mattmdjaga/segformer_b2_clothes')"

COPY app.py color_extraction.py ./
COPY services/ services/
COPY utils/ utils/

ENV PORT=8080
EXPOSE 8080
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}

