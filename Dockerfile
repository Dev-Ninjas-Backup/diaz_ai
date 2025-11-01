FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY requirements.txt .

RUN uv pip install --system -r requirements

COPY . .

EXPOSE 8080

CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--workers", "4", "--bind", "0.0.0.0:8080"]

