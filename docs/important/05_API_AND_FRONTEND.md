# API and Frontend - Complete Guide

**Everything about the FastAPI application, frontend interface, deployment, and search options**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [API Architecture](#api-architecture)
3. [API Endpoints](#api-endpoints)
4. [Frontend Interface](#frontend-interface)
5. [Search Options Explained](#search-options-explained)
6. [Deployment](#deployment)
7. [Security](#security)
8. [Configuration](#configuration)

---

## Overview

**Goal:** Provide REST API and web interface for multi-user access.

**What We Built:**
- ✅ FastAPI application with search and RAG endpoints
- ✅ Simple HTML/JavaScript frontend
- ✅ Service layer (SearchService, RAGService)
- ✅ Error handling and logging
- ✅ Designed for server deployment (one server, multiple users)

**Result:** Complete API ready for internal server deployment

---

## API Architecture

### Design Philosophy

**One Server, Multiple Users:**
- Server runs 24/7
- Model loads once, shared by all users
- Database stays internal (no external access)
- Users connect via their own clients

### Component Structure

```
┌─────────────────────────────────────────┐
│     FastAPI Application (api/app.py)     │
│  ┌───────────────────────────────────┐  │
│  │  SearchService                     │  │
│  │  - Always ready (no LLM needed)   │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  RAGService                        │  │
│  │  - Lazy load model (on first use) │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
           │
           │ Internal Network Only
           │
    ┌──────┴──────┬──────────┬──────────┐
    │             │          │          │
┌───▼───┐   ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│User 1 │   │User 2 │  │User 3 │  │User N │
│Client │   │Client │  │Client │  │Client │
└───────┘   └───────┘  └───────┘  └───────┘
```

### Service Layer

**SearchService:**
- Handles search queries (no LLM needed)
- Uses query parser and embedding model
- Returns results + total count

**RAGService:**
- Handles RAG queries (with optional LLM)
- Lazy loads LLM model on first use
- Returns answer + requests

**Key File:** `api/services.py` - Service layer implementation

---

## API Endpoints

### GET `/api/health`

**Purpose:** Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "search_system": "ready",
  "rag_system": "lazy loading"
}
```

**Usage:**
```bash
curl http://localhost:8000/api/health
```

---

### POST `/api/search`

**Purpose:** Search requests using semantic similarity (no LLM).

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
  "results": [
    {
      "requestid": "211000001",
      "similarity": 0.95,
      "boost": 2.0,
      "projectname": "פרויקט יניב בדיקת הדרכות",
      "updatedby": "אור גלילי",
      ...
    },
    ...
  ],
  "total_found": 34,
  "search_time_ms": 150.5
}
```

**Usage:**
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"query": "פניות מאור גלילי", "top_k": 10}'
```

**Speed:** ⚡ Very fast (~3-5 seconds, no LLM needed)

---

### POST `/api/rag/query`

**Purpose:** RAG query with optional LLM generation.

**Request:**
```json
{
  "query": "כמה פניות יש מיניב ליבוביץ?",
  "top_k": 20,
  "use_llm": true
}
```

**Response (with LLM):**
```json
{
  "query": "כמה פניות יש מיניב ליבוביץ?",
  "answer": "נמצאו 225 פניות של יניב ליבוביץ. הפניות כוללות...",
  "requests": [...],
  "intent": "person",
  "entities": {"person_name": "יניב ליבוביץ"},
  "total_retrieved": 20,
  "response_time_ms": 5000.0,
  "model_loaded": true
}
```

**Response (retrieval only, use_llm=false):**
```json
{
  "query": "כמה פניות יש מיניב ליבוביץ?",
  "answer": null,
  "requests": [...],
  "intent": "person",
  "entities": {"person_name": "יניב ליבוביץ"},
  "total_retrieved": 20,
  "response_time_ms": 150.5,
  "model_loaded": false
}
```

**Usage:**
```bash
# With LLM (slower first time)
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"query": "כמה פניות יש מיניב ליבוביץ?", "use_llm": true}'

# Retrieval only (fast)
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"query": "כמה פניות יש מיניב ליבוביץ?", "use_llm": false}'
```

**Speed:**
- First time (with LLM): 🐌 Slow (~2-5 minutes) - loads model
- Subsequent (with LLM): ⚡ Fast (~5-15 seconds) - model cached
- Retrieval only: ⚡ Very fast (~3-5 seconds) - no LLM

---

## Frontend Interface

### Overview

**Simple HTML/JavaScript interface** for demo and testing.

**Location:** `api/frontend/`

**Files:**
- `index.html` - Main interface
- `style.css` - Styling
- `app.js` - API calls and UI logic

### Features

**Three Search Options:**
1. **חיפוש בלבד** (Search Only) - Fast, no LLM
2. **RAG - רק חיפוש** (RAG Retrieval Only) - Fast, uses RAG infrastructure
3. **RAG - עם תשובה מלאה** (Full RAG) - Slow first time, generates answers

**Display:**
- Query input (Hebrew/English)
- Results list with request details
- Total count display
- Loading messages
- Error handling

**Access:**
- Open `http://localhost:8000` when server is running
- Frontend is served directly from FastAPI server

---

## Search Options Explained

### Option 1: חיפוש בלבד (Search Only)

**What it does:**
- Uses **embedding model only** (lightweight, ~80MB)
- Converts query to vector (384 dimensions)
- Searches database using vector similarity
- Returns list of matching requests
- **No LLM involved** - just search

**Speed:** ⚡ Very fast (~3-5 seconds)

**Model used:** Embedding model only (always loaded, small)

**Output:** List of requests, no text answer

**When to use:**
- ✅ You want fast results
- ✅ You just need a list of requests
- ✅ You don't need a text answer
- ✅ You're exploring/searching

---

### Option 2: RAG - רק חיפוש (RAG Retrieval Only)

**What it does:**
- Uses **same search as Option 1** but through RAG system
- Uses embedding model for search
- **No LLM involved** - just retrieval
- Returns list of matching requests

**Speed:** ⚡ Very fast (~3-5 seconds)

**Model used:** Embedding model only

**Output:** List of requests, no text answer

**Difference from Option 1:** Uses RAG infrastructure, but same result

**When to use:**
- ✅ Same as Option 1
- ✅ You want to test RAG system
- ✅ You're preparing for Option 3

---

### Option 3: RAG - עם תשובה מלאה (Full RAG)

**What it does:**
- Uses **embedding model** for search (same as Option 1)
- Uses **LLM model** (Mistral-7B) to generate text answer
- Combines search + generation = RAG (Retrieval-Augmented Generation)

**Speed:**
- First time: 🐌 Slow (~2-5 minutes) - loads LLM model
- Subsequent: ⚡ Fast (~5-15 seconds) - model already loaded

**Models used:**
- Embedding model (for search)
- LLM model (Mistral-7B, ~4-8GB RAM)

**Output:** Text answer + list of requests

**When to use:**
- ✅ You want a text answer
- ✅ You're asking "how many?", "what?", "which?"
- ✅ You want a summary
- ✅ You're okay waiting 2-5 minutes first time

---

## Deployment

### Architecture

**Recommended: One Internal Server**

```
┌─────────────────────────────────────────┐
│     Internal Server (24/7)               │
│  ┌───────────────────────────────────┐  │
│  │  FastAPI Server (Port 8000)        │  │
│  │  - Search Service (always ready)  │  │
│  │  - RAG Service (lazy load model)  │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  PostgreSQL + pgvector            │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │  LLM Model (Mistral-7B)           │  │
│  │  - Loads once on first query      │  │
│  │  - Stays in memory (shared)       │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
           │
           │ Internal Network Only
           │
    ┌──────┴──────┬──────────┬──────────┐
    │             │          │          │
┌───▼───┐   ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│User 1 │   │User 2 │  │User 3 │  │User N │
│Client │   │Client │  │Client │  │Client │
└───────┘   └───────┘  └───────┘  └───────┘
```

### Benefits

1. **One Model Load** - Model loads once, shared by all users
2. **Better Performance** - Model stays in memory
3. **Centralized Management** - Easy updates, monitoring
4. **Resource Efficient** - One server vs. many local installs
5. **Security** - Database stays internal, no external access

### Server Requirements

**Minimum:**
- CPU: 4+ cores
- RAM: 16GB+ (for model + system)
- Storage: 50GB+ (model + database)
- OS: Windows Server or Linux

**Recommended:**
- CPU: 8+ cores
- RAM: 32GB+ (better performance)
- Storage: 100GB+ SSD
- GPU: Optional but recommended (faster inference)

### Setup Steps

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
   - Via web interface (`http://internal-server:8000`)
   - Via API clients
   - Internal network only

**Key File:** `api/DEPLOYMENT_GUIDE.md` - Complete deployment guide

---

## Security

### Network Isolation

- **Server on internal network only**
- **No internet exposure**
- **Firewall rules** - Only allow internal IPs
- **VPN access** if remote workers need access

### Authentication

- **API keys** - Simple, works for internal use
- **Can upgrade to:** JWT, OAuth2, internal auth system
- **Rate limiting** - Prevent abuse

### Database Security

- **PostgreSQL on same server** (or internal network)
- **No external connections**
- **Strong passwords**
- **Regular backups**

### No External Services

- **No cloud APIs** - Everything runs internally
- **No data leaves the network**
- **Complete privacy**

---

## Configuration

### Environment Variables

**File:** `.env`

```env
# API Configuration
API_KEYS=key1,key2,key3
REQUIRE_AUTH=false  # Set to true in production
ALLOWED_ORIGINS=http://localhost:3000,http://internal-server:3000

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DATABASE=ai_requests_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

### CORS Settings

**Location:** `api/app.py`

**Current:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**For production:**
```python
allow_origins=["http://internal-server:3000", "http://10.0.0.0/8"]
```

### Port Configuration

**Location:** `api/start_server.ps1`, `api/app.py`

**Current:** Port 8000

**How to change:**
```python
# In start_server.ps1 or uvicorn command
uvicorn api.app:app --host 127.0.0.1 --port 8000
# Change 8000 to your desired port
```

---

## Running Locally

### Start Server

**Windows:**
```powershell
.\api\start_server.ps1
```

**Or manually:**
```powershell
cd api
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

### Access Frontend

**Open browser:**
```
http://localhost:8000
```

**Frontend is served directly from FastAPI server** (no CORS issues)

### Test API

**Health check:**
```bash
curl http://localhost:8000/api/health
```

**Search:**
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "פניות מאור גלילי"}'
```

---

## Summary

**Complete API System:**
1. FastAPI application with search and RAG endpoints
2. Service layer (SearchService, RAGService)
3. Simple HTML/JavaScript frontend
4. Designed for server deployment
5. Security considerations (internal network, API keys)
6. Error handling and logging

**Key Points:**
- One server, multiple users
- Model loads once, shared by all
- Search works immediately (no LLM needed)
- RAG loads model on first use (lazy loading)
- Frontend served from API server

**Key Files:**
- `api/app.py` - Main FastAPI application
- `api/services.py` - Service layer
- `api/models.py` - Request/response models
- `api/frontend/` - Frontend files
- `api/DEPLOYMENT_GUIDE.md` - Deployment guide

---

**Last Updated:** Current Session  
**Status:** Complete and tested

