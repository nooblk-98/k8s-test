FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app
RUN useradd -m -u 10001 appuser
COPY --from=builder /opt/venv /opt/venv
COPY app ./app
USER appuser
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
