# Diaz AI — repository overview and run instructions

This README reflects the current repository layout and run instructions for the Diaz AI boat-sales conversational assistant (FastAPI + LangGraph + OpenAI + Qdrant + Elasticsearch).

Last updated: 2025-12-16

---

## Project layout (important files & folders)

Top-level:

```
any_test.py
docker-compose.yml
Dockerfile
main.py
pyproject.toml
requirements.txt
README.md
app/
config/
database/
indexDatabase/
logs/
reverse_proxy/
diaz_server_file/
```

app/ (key folders)

- `app/api/v1/endpoints/` — `chat_endpoint.py`, `search_endpoint.py` (FastAPI routes)
- `app/services/chatbot/` — core chatbot logic (chat orchestration, graph, llms, memory, nodes, retriever, data_pipeline)
- `app/services/search_engine/` — Elasticsearch-based search and indexing code
- `app/schemas/schema.py` — Pydantic models (ChatRequest, ChatResponse, Message, etc.)
- `app/utils/` — logger, helper, prompt, and other utilities
- `app/config.py` — loads `config/config.yaml` and `.env`
│   │   │   └── states/
│   │   │       └── state.py          # ChatState - LangGraph state schema
│   │   │
│   │   └── search_engine/
│   │       ├── search.py             # SearchEngine - Elasticsearch semantic search
│   │       ├── data_indexing_pipeline.py  # Elasticsearch indexing pipeline
│   │       └── index_mapping.py      # Elasticsearch index mapping configuration
│   │
│   ├── schemas/
│   │   └── schema.py                 # Pydantic models (ChatRequest, ChatResponse, SearchModel, etc.)
│   │
│   ├── utils/
│   │   ├── logger.py                 # Logging configuration
│   │   ├── prompt.py                 # System prompts and templates
│   │   ├── helper.py                 # Helper utilities (request_data, save_json, load_json, etc.)
│   │   └── __init__.py
│   │
│   ├── config.py                     # Configuration loader (loads config.yaml and .env)
│   └── __init__.py
│
├── config/
│   └── config.yaml                   # Application configuration (APIs, Qdrant, Elasticsearch, OpenAI)
│
├── database/
│   ├── raw_json_data/                # Raw API responses (boat_data_0.json, boat_data_1.json, etc.)
│   └── process_csv_data/             # Processed boat data as CSV
│
├── indexDatabase/
│   └── index_vector_data.csv         # Pre-indexed vector data for Elasticsearch
│
├── logs/                             # Application logs directory
│
├── reverse_proxy/
│   └── nginx.conf                    # Nginx reverse proxy configuration
│
├── diaz_server_file/
│   ├── docker-compose.yml            # Server environment docker-compose
│   └── reverse_proxy/
│       └── nginx.conf                # Nginx config for server
│
├── main.py                           # FastAPI application entry point
├── pyproject.toml                    # Python project dependencies and metadata
├── requirements.txt                  # pip dependencies list
├── docker-compose.yml                # Docker Compose for local development
├── Dockerfile                        # Docker image definition
└── README.md                         # This file
```

## 🗂️ Key Components

### API Endpoints (`app/api/v1/endpoints/`)

#### Chat Endpoints (`chat_endpoint.py`)
- **`POST /chat`**: Send a message and get a response
  - Request: `ChatRequest` (messages, user_id, session_id)
  - Response: Chat response + session_id for tracking
  
- **`POST /chat_history`**: Retrieve conversation history
  - Request: `HistoryModel` (user_id, session_id)
  - Response: List of messages with roles (user/assistant)

#### Search Endpoints (`search_endpoint.py`)
- **`POST /search_boat`**: Search for boats using semantic search
  - Request: `SearchModel` (query, k)
  - Response: Top-k relevant boats with details and links

### Core Services

#### ChatBot Service (`app/services/chatbot/`)

**1. Chat Function** (`chat_function/chat.py`)
- `InitChat` class manages the main chat orchestration
- Initializes the LLM, graph, and checkpointer
- Methods:
  - `initialize_chat()`: Setup LangGraph workflow
  - `chat(prompt, thread_id)`: Send message and get response
  - `get_chat_history(thread_id)`: Retrieve conversation history

**2. Data Pipeline** (`data_pipeline/dataflow_pipeline.py`)
- `VectorDataBase` class handles ETL for boat data
- Steps:
  1. `collect_data()`: Fetch from external boat APIs
  2. `merge_data()`: Combine multiple API responses
  3. `process_data()`: Clean, filter, and transform (remove HTML, add links)
  4. `chunking_data()`: Convert rows to LangChain Documents
  5. `vectorize_data()`: Embed and store in Qdrant
  6. `init_vector_database()`: Initialize Qdrant collection

**3. Graph Builder** (`graph/graph_builder.py`)
- `GraphBuilder` constructs the LangGraph workflow
- Creates a simple graph: START → chatbot node → END
- Compiles with checkpoint support for state persistence

**4. LLM & Embeddings** (`llms/open_ai_llm.py`)
- `OpenaiLLM` class wraps OpenAI configuration
- Provides:
  - GPT-4o-mini for chat
  - text-embedding-3-large for vector embeddings (3072 dimensions)

**5. Retriever** (`retriever/qdrant_retriever.py`)
- `Retriever` class connects to Qdrant vector database
- Methods:
  - `initialize_retriever()`: Create Qdrant client
  - `get_retriever()`: Create LangChain retriever for similarity search (top-5)

**6. Nodes** (`nodes/node.py`)
- `ChatbotNodes` defines graph node logic
- Invokes the LLM with context from retriever

**7. State Management** (`states/state.py`)
- `ChatState` defines the LangGraph state schema
- Holds messages and any other stateful data

#### Search Engine Service (`app/services/search_engine/`)

**1. Search** (`search.py`)
- `SearchEngine` class for semantic search via Elasticsearch
- Queries:
  - Converts user query to embeddings
  - Performs k-NN search in Elasticsearch
  - Returns top-k boats with details

**2. Data Indexing Pipeline** (`data_indexing_pipeline.py`)
- Prepares and indexes boat data in Elasticsearch

**3. Index Mapping** (`index_mapping.py`)
- Defines Elasticsearch schema and field mappings

### Configuration

**`config/config.yaml`**
- OpenAI settings (model, temperature, embedding model)
- API endpoints for boat data sources
- Database locations (raw_json_data, process_csv_data)
- Qdrant vector database configuration:
  ```yaml
  vector:
    url: "http://localhost:6333"
    collection_name: "boat_vector_data"
    dim_size: 3072
  ```
- Elasticsearch configuration:
  ```yaml
  search:
    elastic_url: "https://localhost:9200"
    user: "elastic"
    pass: "xARs94-gKY_Sc3gZSCzv"
    index_name: "boat_data"
  ```

## 📋 Prerequisites

- **Python 3.13+** (as specified in `pyproject.toml`)
- **OpenAI API Key** (for GPT-4o-mini and embeddings)
- **Qdrant Vector Database** (for semantic search and RAG)
- **Elasticsearch 9.2+** (for boat inventory search)
- **Docker & Docker Compose** (optional, for containerized deployment)

## ⚡ Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Softvence-Omega-Dev-Ninjas/diaz_ai.git
cd diaz_ai
```

### 2. Environment Setup

#### Option A: Using `uv` (Recommended)

```bash
# Install with uv
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

#### Option B: Using `pip`

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create `.env` file in the project root:

```env
OPENAI_API_KEY="sk-your-actual-openai-api-key-here"
```

**Configure services** in `config/config.yaml`:

```yaml
openai:
  model: "gpt-4o-mini"
  temperature: 0.7
  embedding_model: "text-embedding-3-large"

vector:
  url: "http://localhost:6333"        # Qdrant server URL
  collection_name: "boat_vector_data"
  dim_size: 3072

search:
  elastic_url: "https://localhost:9200"
  user: "elastic"
  pass: "xARs94-gKY_Sc3gZSCzv"
  index_name: "boat_data"

api:
  api_1: "https://services.boats.com/pls/boats/search?key=..."
  api_2: "https://api.boats.com/inventory/search?key=..."
```

### 4. Start External Services

#### Qdrant Vector Database

**Option A: Docker (Quick)**
```bash
docker run -d --name qdrant \
  -p 6333:6333 -p 6334:6334 \
  -v qdrant_data:/qdrant/storage \
  qdrant/qdrant:latest
```

**Option B: Docker Compose**
```bash
# Add to docker-compose.yml and run
docker-compose up -d qdrant
```

#### Elasticsearch (Optional for Search)

```bash
docker run -d --name elasticsearch \
  -p 9200:9200 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enrollment.enabled=false" \
  docker.elastic.co/elasticsearch/elasticsearch:9.2.0
```

### 5. Run Application

**Development Mode** (with auto-reload):
```bash
python main.py
# or
uvicorn main:app --reload --host localhost --port 8000
```

**Production Mode**:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at `http://localhost:8000`

**Interactive API Documentation**:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 6. (Optional) Load Data Pipeline

Initialize Qdrant collection and vectorize boat data:

```bash
python -c "
import asyncio
from app.services.chatbot.data_pipeline.dataflow_pipeline import VectorDataBase

async def run():
    pipeline = VectorDataBase()
    await pipeline.collect_data()
    pipeline.merge_data()
    pipeline.process_data()
    await pipeline.vectorize_data()

asyncio.run(run())
"
```

## 🐳 Docker Deployment

### Run with Docker Compose

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f diaz_fastapi

# Stop services
docker-compose down
```

**`docker-compose.yml` includes**:
- FastAPI application (port 8080)
- Nginx reverse proxy (port 80)
- Automatic dependency management

### Manual Docker Build

```bash
# Build image
docker build -t diaz_ai_app:latest .

# Run container
docker run -d \
  --name diaz_app \
  -p 8000:8000 \
  -e OPENAI_API_KEY="your-key" \
  --network host \
  diaz_ai_app:latest
```

## 📚 API Documentation

### Base URL

```
http://localhost:8000
```

### Authentication

Currently, all endpoints are **public** (CORS enabled for all origins). For production, implement:
- API Key validation
- JWT tokens
- Rate limiting

### Endpoints

#### 1. Chat Endpoint

**POST** `/chat`

Send a message and receive an AI response based on boat inventory data.

**Request Body**:
```json
{
  "messages": "What boats do you have under $100,000?",
  "user_id": "user123",
  "session_id": "session_456"
}
```

**Response** (200 OK):
```json
{
  "messages": "Based on our inventory, here are the best options under $100,000...",
  "session_id": "session_456"
}
```

**Error** (500):
```json
{
  "detail": "Failed to initialize Qdrant client: Connection refused"
}
```

---

#### 2. Chat History Endpoint

**POST** `/chat_history`

Retrieve the conversation history for a user session.

**Request Body**:
```json
{
  "user_id": "user123",
  "session_id": "session_456"
}
```

**Response** (200 OK):
```json
[
  {
    "role": "user",
    "content": "What boats do you have?"
  },
  {
    "role": "assistant",
    "content": "We have several options..."
  }
]
```

---

#### 3. Search Boat Endpoint

**POST** `/search_boat`

Perform semantic search across boat inventory using Elasticsearch.

**Request Body**:
```json
{
  "query": "fast luxury yacht",
  "k": 5
}
```

**Response** (200 OK):
```json
[
  {
    "id": "boat_12345",
    "make": "Sunseeker",
    "model": "55 Yacht",
    "price": "$250,000",
    "location": "Miami, FL",
    "link": "https://development.jupitermarinesales.com/search-listing/boat_12345"
  }
]
```

---

### cURL Examples

**Chat Request**:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": "Show me sailboats",
    "user_id": "john_doe",
    "session_id": "session_001"
  }'
```

**Chat History Request**:
```bash
curl -X POST "http://localhost:8000/chat_history" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "john_doe",
    "session_id": "session_001"
  }'
```

**Search Request**:
```bash
curl -X POST "http://localhost:8000/search_boat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "catamaran cruiser",
    "k": 10
  }'
```

---

### Python Client Examples

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Send a chat message
response = requests.post(f"{BASE_URL}/chat", json={
    "messages": "What's the best boat for beginners?",
    "user_id": "alice",
    "session_id": "sess_001"
})
print(response.json())

# 2. Get chat history
response = requests.post(f"{BASE_URL}/chat_history", json={
    "user_id": "alice",
    "session_id": "sess_001"
})
print(json.dumps(response.json(), indent=2))

# 3. Search for boats
response = requests.post(f"{BASE_URL}/search_boat", json={
    "query": "luxury motor yacht",
    "k": 5
})
print(json.dumps(response.json(), indent=2))
```

## 🔧 Configuration Details

### `config/config.yaml`

```yaml
# OpenAI LLM and Embeddings Configuration
openai:
  model: "gpt-4o-mini"              # Chat model
  temperature: 0.7                   # Creativity level (0=deterministic, 1=creative)
  embedding_model: "text-embedding-3-large"  # For semantic embeddings (3072 dims)

# Qdrant Vector Database
vector:
  url: "http://localhost:6333"       # Qdrant HTTP API endpoint
  collection_name: "boat_vector_data" # Collection for boat vectors
  dim_size: 3072                     # Embedding dimension (must match model output)

# Elasticsearch for Search
search:
  elastic_url: "https://localhost:9200"
  user: "elastic"
  pass: "xARs94-gKY_Sc3gZSCzv"
  index_name: "boat_data"

# External Boat Data APIs
api:
  api_1: "https://services.boats.com/pls/boats/search?key=..."
  api_2: "https://api.boats.com/inventory/search?key=..."

# Database Locations
database_loc:
  raw_data_loc: "database/raw_json_data/"
  process_data_loc: "database/process_csv_data/"

# Data Fields to Keep During Processing
columns:
  keep: [
    "GeneralBoatDescription",
    "AdditionalDetailDescription",
    "DocumentID",
    "MakeString",
    "Model",
    "ModelYear",
    "BoatLocation",
    "BoatCityNameNoCaseAlnumOnly",
    "Price",
    "NominalLength",
    "LengthOverall",
    "BeamMeasure",
    "Engines",
    "TotalEnginePowerQuantity",
    "NumberOfEngines",
    "Images"
  ]
```

### Environment Variables

| Variable           | Description                     | Example                          | Required |
| ------------------ | ------------------------------- | -------------------------------- | -------- |
| `OPENAI_API_KEY`   | OpenAI API key                  | `sk-...`                         | ✅       |
| `QDRANT_URL`       | Qdrant server endpoint (optional override) | `http://qdrant:6333` | ❌       |
| `ELASTICSEARCH_URL`| Elasticsearch endpoint (optional) | `https://elasticsearch:9200`    | ❌       |

## 🔄 Data Pipeline Workflow

The data pipeline orchestrates boat data collection, processing, and indexing:

```
1. collect_data()      → Fetch from external APIs → database/raw_json_data/
                          ↓
2. merge_data()        → Combine multiple sources → boat_data_all.json
                          ↓
3. process_data()      → Clean, filter, transform → database/process_csv_data/process_data.csv
                          - Remove HTML tags
                          - Filter to relevant columns
                          - Add direct links to listings
                          ↓
4. chunking_data()     → Convert rows to Documents → LangChain Documents
                          ↓
5. init_vector_database() → Create Qdrant collection with COSINE distance
                          ↓
6. vectorize_data()    → Embed using OpenAI & store → Qdrant collection
```

## 🧠 Chatbot Architecture

```
User Input
    ↓
[API Endpoint: /chat]
    ↓
[InitChat.chat(prompt, thread_id)]
    ↓
[LangGraph Workflow]
    ├─→ GraphBuilder.chatbot_graph()
    │   └─→ START → ChatbotNodes.invoke_chat → END
    │
    ├─→ ChatbotNodes retrieves context:
    │   └─→ Retriever → Qdrant (similarity search, top-5)
    │
    ├─→ Passes to LLM (GPT-4o-mini):
    │   ├─ System Prompt (from prompt.py)
    │   ├─ Retrieved Boat Context
    │   └─ User Query
    │
    ├─→ LLM generates response
    │
    └─→ State stored in MemorySaver (checkpointer)
    ↓
[Response returned to client]
```

## 📊 Monitoring & Logging

### Log Configuration

- **Log Directory**: `logs/`
- **Format**: Timestamp | Level | Module | Message
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

### Viewing Logs

```bash
# See all logs
tail -f logs/*.log

# Filter by level
grep "ERROR" logs/*.log

# Real-time monitoring
watch -n 1 'tail -20 logs/*.log'
```

### Key Log Points

- API endpoint invocations
- Qdrant client initialization and queries
- Elasticsearch connections
- Data pipeline progress (collect, merge, process, vectorize)
- LLM invocations and token usage
- Error stack traces with context

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest test_root.py -v
```

### Manual Testing

```python
# Test chat
from app.services.chatbot.chat_function.chat import InitChat
import asyncio

async def test():
    chat = InitChat()
    await chat.initialize_chat()
    response = await chat.chat("Hello!", "user1_sess1")
    print(response)

asyncio.run(test())
```

## 🔐 Security Considerations

### Production Checklist

- [ ] Set `CORS_ORIGINS` to specific domains (not `["*"]`)
- [ ] Use environment variables for all secrets (API keys, passwords)
- [ ] Enable HTTPS/TLS for API endpoints
- [ ] Implement API key or JWT authentication
- [ ] Add rate limiting per user/IP
- [ ] Use strong Elasticsearch passwords
- [ ] Validate and sanitize user inputs
- [ ] Enable audit logging for sensitive operations
- [ ] Use network policies to restrict service access
- [ ] Regularly update dependencies (`pip install --upgrade`)

### Current State

⚠️ **Note**: The current implementation has CORS enabled for all origins. For production use, update `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domains only
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)
```

## 🚀 Deployment

### Option 1: Docker Compose (Recommended for Development)

```bash
docker-compose up -d
```

### Option 2: Kubernetes

See `diaz_server_file/` for example configurations.

### Option 3: Manual VPS Deployment

1. Set up Python 3.13 environment
2. Clone repository
3. Configure `.env` and `config/config.yaml`
4. Start Qdrant and Elasticsearch services
5. Run: `uvicorn main:app --host 0.0.0.0 --port 8000`
6. Configure Nginx reverse proxy (see `reverse_proxy/nginx.conf`)

## 📖 System Prompts

The chatbot uses a specialized system prompt (defined in `app/utils/prompt.py`) that instructs the AI to:

- Greet customers warmly
- Ask clarifying questions about boat preferences
- Provide clickable links to boat listings
- Include boat images where available
- Focus on key selling points (brand, year, features, price, location)
- Maintain a friendly, professional tone
- Restrict responses to boat-related topics

Example System Prompt:
```
You are a professional, friendly, and persuasive AI chatbot representing a boat seller's 
online assistant. Your goal is to interact with potential buyers naturally...

[Full prompt in app/utils/prompt.py]
```

## 🐛 Troubleshooting

### Issue: Qdrant Connection Refused

**Solution**:
```bash
# Check if Qdrant is running
curl http://localhost:6333/health

# Start Qdrant if not running
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest
```

### Issue: OpenAI API Key Invalid

**Solution**:
```bash
# Verify key is set
echo $OPENAI_API_KEY  # Should not be empty

# Update .env file with correct key
# Restart application
```

### Issue: Elasticsearch Connection Error

**Solution**:
```bash
# Start Elasticsearch
docker run -d --name elasticsearch -p 9200:9200 \
  -e "discovery.type=single-node" \
  docker.elastic.co/elasticsearch/elasticsearch:9.2.0
```

### Issue: Chat Returns Empty Response

**Possible causes**:
- Qdrant collection not initialized (run data pipeline)
- No boat data in Qdrant collection
- LLM token limit exceeded
- API rate limit hit

**Debug**:
```python
from qdrant_client import QdrantClient
client = QdrantClient(url="http://localhost:6333")
print(client.get_collections())
```

## 📚 Dependencies

Key dependencies (see `pyproject.toml` for full list):

| Package | Version | Purpose |
| ------- | ------- | ------- |
| `fastapi` | >=0.120.2 | Web framework |
| `langchain` | >=1.0.2 | LLM orchestration |
| `langgraph` | >=1.0.2 | Workflow graphs |
| `qdrant-client` | >=1.15.1 | Vector database client |
| `langchain-qdrant` | >=1.1.0 | Qdrant integration |
| `elasticsearch` | >=9.2.0 | Search engine |
| `langchain-openai` | >=1.0.1 | OpenAI integration |
| `pydantic` | >=2.12.3 | Data validation |
| `pandas` | >=2.3.3 | Data processing |

## 📝 License

This project is proprietary software developed by **Softvence-Omega-Dev-Ninjas**.

## 📧 Support & Contact

For issues, questions, or contributions:
- **Email**: dev@softvence.com
- **GitHub Issues**: [Create an issue](https://github.com/Softvence-Omega-Dev-Ninjas/diaz_ai/issues)
- **Repository**: https://github.com/Softvence-Omega-Dev-Ninjas/diaz_ai

---

**Built with ❤️ using FastAPI, LangGraph, Qdrant, OpenAI, and Elasticsearch**

_Last Updated: November 2025_
