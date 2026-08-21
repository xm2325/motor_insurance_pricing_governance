FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_BUNDLE_DIR=/models

WORKDIR /app

COPY requirements-runtime.txt ./
RUN pip install --no-cache-dir -r requirements-runtime.txt

COPY deployment ./deployment

EXPOSE 8000
CMD ["uvicorn", "deployment.app:app", "--host", "0.0.0.0", "--port", "8000"]
