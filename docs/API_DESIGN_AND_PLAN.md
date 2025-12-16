# API Design & Deployment Plan

## 🎯 What We Agreed On

### Architecture: One Server, Multiple Users

**Deployment Model:**
```
┌─────────────────────────────────────────┐
│   Internal Company Server (24/7)        │
│   - FastAPI running on port 8000        │
│   - PostgreSQL database                 │
│   - LLM model (loads once, shared)      │
│   - Internal network only                │
└─────────────────────────────────────────┘
           │
           │ Internal Network
           │
    ┌──────┴──────┬──────────┬──────────┐
    │             │          │          │
┌───▼───┐   ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│User 1 │   │User 2 │  │User 3 │  │User N │
│PC     │   │PC     │  │PC     │  │PC     │
└───────┘   └───────┘  └───────┘  └───────┘
```

**Key Points:**
- ✅ **One server** runs the API 24/7
- ✅ **Multiple users** connect from their own PCs
- ✅ **Model loads once** - shared by all users
- ✅ **Database stays internal** - on server or internal network
- ✅ **No external internet** - everything internal
- ✅ **API keys** - simple authentication

---

## 🔒 Security Model

### Internal Network Only
- **No internet exposure** - API only accessible on internal network
- **Firewall rules** - Only allow internal IPs
- **Database isolation** - PostgreSQL on same server or internal network
- **No external APIs** - Everything runs internally

### Authentication
- **API keys** - Simple, works for internal use
- **Can upgrade to:** JWT, OAuth2, internal auth system
- **Rate limiting** - Prevent abuse (can add later)

---

## 🧪 Testing Locally vs Production

### Local Testing (Your PC Now)
**What it is:**
- Run API on your PC: `python api/app.py`
- Test with browser/Postman/curl
- Same code, same functionality
- Model loads once (like on server)

**Why it works:**
- ✅ Same code works on server
- ✅ Can test everything
- ✅ Verify it works before deployment
- ⚠️ Only you can access (localhost)

**Use for:**
- Development
- Testing
- Verification
- Learning

### Production Deployment (Client's Server)
**What it is:**
- Install on internal company server
- Run 24/7 as a service
- Multiple users connect via internal network
- Model loads once, shared by all

**Why it's better:**
- ✅ Multiple users can access
- ✅ Model loads once (efficient)
- ✅ Centralized management
- ✅ Better security (internal network)

**Use for:**
- Production
- Client deployment
- Real usage

---

## 📋 Current API Design

### Endpoints Created

1. **GET `/api/health`**
   - Health check
   - Shows system status
   - No authentication needed

2. **POST `/api/search`**
   - Semantic search (no LLM)
   - Fast (<1 second)
   - Works immediately
   - Returns list of requests

3. **POST `/api/rag/query`**
   - Full RAG with optional LLM
   - `use_llm=false` - Retrieval only (fast)
   - `use_llm=true` - With LLM generation (slower first time)
   - Returns answer + requests

4. **GET `/api/requests/{request_id}`**
   - Get full details of specific request

### Features

- ✅ **Multi-user support** - Stateless, connection pooling
- ✅ **Model sharing** - Loads once, reused by all
- ✅ **Lazy loading** - Model loads on first RAG query with LLM
- ✅ **Error handling** - Comprehensive error messages
- ✅ **Logging** - All queries logged
- ✅ **Authentication** - API keys (simple, can upgrade)

---

## 🚀 Deployment Plan

### Phase 1: Local Testing (Now)
- ✅ Test API on your PC
- ✅ Verify all endpoints work
- ✅ Test with real queries
- ✅ Fix any issues

### Phase 2: Build Frontend (Next)
- Build web interface
- Connects to API
- Can test locally first
- Then deploy to server

### Phase 3: Server Deployment (For Client)
- Install on internal server
- Configure for internal network
- Set up as service (24/7)
- Users connect via web interface

---

## ✅ Summary

**What we agreed:**
- ✅ One internal server (24/7)
- ✅ Multiple users connect from their PCs
- ✅ Model loads once, shared
- ✅ Database internal
- ✅ No external internet
- ✅ API keys for auth

**Current state:**
- ✅ API built and ready
- ✅ Can test locally on your PC
- ✅ Same code works on server

**Next steps:**
- Test API locally
- Build frontend
- Deploy to server when ready

**The API is designed for internal server deployment, but works perfectly for local testing!**

