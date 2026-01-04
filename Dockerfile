FROM python:3.12-slim

RUN useradd -m appuser


WORKDIR /app

RUN pip install uv

COPY requirements.txt .

RUN  pip install --no-cache -r requirements.txt

COPY . .

USER appuser

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]


