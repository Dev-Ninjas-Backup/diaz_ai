FROM python:3.12-slim


WORKDIR /app

RUN pip install uv

COPY requirements.txt .

RUN  pip install --no-cache -r requirements.txt

# Create non-root user
RUN useradd -m appuser

# Create logs directory & give ownership
RUN mkdir -p /app/logs && chown -R appuser:appuser /app
COPY . .

USER appuser

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]


