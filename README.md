# Diaz AI — concise overview

- Purpose: AI backend for boat search & chat. Core stack: Python, FastAPI, Celery, Qdrant, OpenAI.
- Target: local development and containerized deployment.

Quick start
- Install dependencies: `pip install -r requirements.txt`
- Run server (dev): `uvicorn main:app --reload`
- Run with Docker: `docker-compose up --build`

Essential workflow
1. Configure environment
   - Create `.env` with `OPENAI_API_KEY` and any secrets.
   - Edit `config/config.yaml` for Qdrant/Elasticsearch/OpenAI values.
2. Start vector DB (Qdrant) and Elasticsearch if using search features.
3. Prepare data
   - Load raw files in `database/raw_json_data*` or run the data pipeline to collect/process data.
   - Vectorize data to populate Qdrant (data pipeline in `app/services/chatbot/data_pipeline`).
4. Start services
   - API: `uvicorn main:app --reload`
   - Celery worker: `celery -A app.celery_app worker -l info`
   - Celery beat (scheduler): `celery -A app.celery_app beat -l info` (if scheduled tasks used)
5. Use API
   - Open interactive docs: `http://localhost:8000/docs`
   - Key endpoints live in `app/api/v1/endpoints`.

Key locations
- API routes: `app/api/v1/endpoints`
- Chatbot pipeline: `app/services/chatbot`
- Search & indexing: `app/services/search_engine`
- Raw data: `database/raw_json_data*`

Testing & maintenance
- Run tests: `pytest`
- Logs: check `logs/` for runtime output

Notes
- Keep secrets out of source control.
- For production: secure endpoints, use managed vector/search services, scale Celery and Uvicorn.



