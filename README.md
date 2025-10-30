# House Price Prediction Chatbot

A production-ready conversational AI system built with FastAPI and LangGraph for real estate price predictions and consultations.

## 🚀 Features

- **Conversational AI**: OpenAI GPT-4o-mini powered chatbot
- **Persistent Memory**: MongoDB-based conversation history
- **Async Architecture**: Non-blocking operations for high performance
- **RESTful API**: FastAPI with automatic OpenAPI documentation
- **Session Management**: Multi-user conversation tracking
- **Scalable Design**: Modular architecture with dependency injection

## 🏗️ Architecture

```
├── app/
│   ├── api/v1/endpoints/     # API route handlers
│   ├── services/chatbot/     # Core chatbot logic
│   │   ├── chat_function/    # Chat orchestration
│   │   ├── graph/           # LangGraph workflow
│   │   ├── llms/            # LLM integrations
│   │   ├── memory/          # Persistence layer
│   │   ├── nodes/           # Graph nodes
│   │   └── states/          # State management
│   ├── schemas/             # Pydantic models
│   └── utils/               # Utilities & logging
├── config/                  # Configuration files
└── logs/                   # Application logs
```

## 📋 Prerequisites

- Python 3.11+
- MongoDB Atlas account
- OpenAI API key
- PostgreSQL (optional)

## ⚡ Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd HousePricePredictionChatbot
```

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Create `.env` file:
```env
OPENAI_API_KEY="your-openai-api-key"
MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/"
DB_NAME="chatbot_memory_db"
POSTGRES_URI="postgresql://user:pass@host:port/db"
NEONDB_NAME="neondb"
```

### 4. Run Application
```bash
# Development
uvicorn main:app --reload

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### Chat
```http
POST /chat
Content-Type: application/json

{
  "messages": "What's the average house price in NYC?",
  "user_id": "user123",
  "session_id": "session456"
}
```

#### Chat History
```http
POST /chat_history
Content-Type: application/json

{
  "user_id": "user123",
  "session_id": "session456"
}
```

#### Delete History
```http
DELETE /delete_chat_history
Content-Type: application/json

{
  "user_id": "user123",
  "session_id": "session456"
}
```

### Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔧 Configuration

### Model Settings (`config/config.yaml`)
```yaml
openai:
  model: "gpt-4o-mini"
  temperature: 0.0

logger:
  log_dir: "logs"
```

### Environment Variables
| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | ✅ |
| `MONGODB_URI` | MongoDB connection string | ✅ |
| `DB_NAME` | MongoDB database name | ✅ |
| `POSTGRES_URI` | PostgreSQL connection string | ❌ |
| `NEONDB_NAME` | PostgreSQL database name | ❌ |

## 🏃‍♂️ Usage Examples

### Python Client
```python
import requests

# Start conversation
response = requests.post("http://localhost:8000/chat", json={
    "messages": "Hello, I'm looking for house prices",
    "user_id": "john_doe",
    "session_id": "session_001"
})

print(response.json())
```

### cURL
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": "What factors affect house prices?",
    "user_id": "jane_smith",
    "session_id": "session_002"
  }'
```

## 📊 Monitoring & Logging

- **Logs Location**: `logs/YYYY-MM-DD.log`
- **Log Levels**: INFO, ERROR, DEBUG
- **Structured Logging**: JSON format with timestamps

## 🔄 Changelog

### v1.0.0
- Initial release
- Basic chat functionality
- MongoDB integration
- Session management

---

**Built with ❤️ using FastAPI, LangGraph, and OpenAI**