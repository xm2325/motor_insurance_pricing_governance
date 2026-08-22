FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MODEL_BUNDLE_DIR=/models

WORKDIR /app

# Apply fixes already published for the current Debian base before installing the
# Python runtime. v0.30's vulnerability gate fails if fixable HIGH findings remain.
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-runtime.txt ./
RUN pip install --no-cache-dir -r requirements-runtime.txt

COPY deployment ./deployment

EXPOSE 8000
CMD ["uvicorn", "deployment.app:app", "--host", "0.0.0.0", "--port", "8000"]
