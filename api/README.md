# RAG System API

FastAPI-based REST API for the AI Requests RAG System.

## 🏗️ Architecture

**Designed for internal server deployment:**
- One server runs 24/7
- Multiple users connect via their own clients
- Model loads once, shared by all users
- Database stays internal (no external access)

## 🔒 Security

- **Internal network only** - No internet exposure
- **API key authentication** - Simple auth (can be upgraded)
- **Database isolation** - No external database connections
- **No external APIs** - Everything runs internally

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
pip install -r api/requirements.txt
```

### 2. Configure Environment

Add to `.env`:
```env
# API Configuration
API_KEYS=key1,key2,key3  # Comma-separated API keys
REQUIRE_AUTH=false  # Set to true in production
ALLOWED_ORIGINS=http://localhost:3000,http://internal-server:3000

# Database (already configured)
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DATABASE=ai_requests_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

### 3. Run API Server

```powershell
cd api
python app.py
```

Or with uvicorn:
```powershell
uvicorn api.app:app --host 0.0.0.0 --port 8000
```

### 4. Test API

**Health check:**
```powershell
curl http://localhost:8000/api/health
```

**Search (no LLM needed):**
```powershell
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"query": "פניות מאור גלילי", "top_k": 10}'
```

**RAG query (retrieval only, fast):**
```powershell
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"query": "כמה פניות יש מיניב ליבוביץ?", "use_llm": false}'
```

**RAG query (with LLM, slower first time):**
```powershell
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"query": "כמה פניות יש מיניב ליבוביץ?", "use_llm": true}'
```

## 📡 API Endpoints

### GET `/api/health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "search_system": "ready",
  "rag_system": "lazy loading"
}
```

### POST `/api/search`
Search requests using semantic similarity (no LLM).

**Request:**
```json
{
  "query": "פניות מאור גלילי",
  "top_k": 20,
  "include_details": true
}
```

**Response:**
```json
{
  "query": "פניות מאור גלילי",
  "intent": "person",
  "entities": {"person_name": "אור גלילי"},
  "results": [...],
  "total_found": 20,
  "search_time_ms": 150.5
}
```

### POST `/api/rag/query`
RAG query with optional LLM generation.

**Request:**
```json
{
  "query": "כמה פניות יש מיניב ליבוביץ?",
  "top_k": 20,
  "use_llm": true
}
```

**Response:**
```json
{
  "query": "כמה פניות יש מיניב ליבוביץ?",
  "answer": "יש 120 פניות...",
  "requests": [...],
  "intent": "person",
  "entities": {"person_name": "יניב ליבוביץ"},
  "total_retrieved": 20,
  "response_time_ms": 5000.0,
  "model_loaded": true
}
```

### GET `/api/requests/{request_id}`
Get full details of a specific request.

## 🔐 Authentication

Currently uses simple API key authentication via `X-API-Key` header.

**For production, consider:**
- JWT tokens
- OAuth2
- Internal authentication system
- Role-based access control

## 📊 Performance

- **Search endpoint:** <1 second (no model loading)
- **RAG with retrieval only:** <1 second
- **RAG with LLM (first query):** 2-5 minutes (model loading)
- **RAG with LLM (subsequent):** 5-15 seconds (model cached)

## 🚀 Deployment

### Internal Server Setup

1. **Install on server:**
   - Python 3.13
   - PostgreSQL + pgvector
   - All dependencies

2. **Configure:**
   - Set `REQUIRE_AUTH=true`
   - Configure `ALLOWED_ORIGINS` for your network
   - Set API keys

3. **Run as service:**
   - Use systemd (Linux) or Windows Service
   - Or use process manager (PM2, supervisor)

4. **Users connect:**
   - Via web interface
   - Via API clients
   - Internal network only

## 🔧 Configuration

All configuration via environment variables (`.env` file).

See `.env.example` for all options.

