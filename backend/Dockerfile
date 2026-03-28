# ====================== Builder stage ======================
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ====================== Runtime stage ======================
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create non-root user with home directory
RUN addgroup --system --gid 1001 django \
    && adduser --system --uid 1001 --ingroup django --home /home/django django

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy project code
COPY --chown=django:django . .

RUN chmod +x entrypoint.sh \
    && mkdir -p staticfiles temp_uploads /home/django/.cache/huggingface \
    && chown -R django:django staticfiles temp_uploads /home/django/.cache

USER django

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
