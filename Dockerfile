FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ai_gateway ./ai_gateway
COPY config ./config
COPY README.md ./

ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "ai_gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
