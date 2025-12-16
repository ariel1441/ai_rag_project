# Deployment Guide - Internal Server Setup

## 🎯 Deployment Architecture

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
│  │  - Requests table                 │  │
│  │  - Embeddings table               │  │
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

## ✅ Benefits of Server Deployment

1. **One Model Load** - Model loads once, shared by all users
2. **Better Performance** - Model stays in memory
3. **Centralized Management** - Easy updates, monitoring
4. **Resource Efficient** - One server vs. many local installs
5. **Security** - Database stays internal, no external access

## 🔒 Security Considerations

### 1. Network Isolation
- **Server on internal network only**
- **No internet exposure**
- **Firewall rules** - Only allow internal IPs
- **VPN access** if remote workers need access

### 2. Authentication
- **API keys** - Simple, works for internal use
- **Can upgrade to:** JWT, OAuth2, internal auth system
- **Rate limiting** - Prevent abuse

### 3. Database Security
- **PostgreSQL on same server** (or internal network)
- **No external connections**
- **Strong passwords**
- **Regular backups**

### 4. No External Services
- **No cloud APIs** - Everything runs internally
- **No data leaves the network**
- **Complete privacy**

## 📋 Server Requirements

### Minimum:
- **CPU:** 4+ cores
- **RAM:** 16GB+ (for model + system)
- **Storage:** 50GB+ (model + database)
- **OS:** Windows Server or Linux

### Recommended:
- **CPU:** 8+ cores
- **RAM:** 32GB+ (better performance)
- **Storage:** 100GB+ SSD
- **GPU:** Optional but recommended (faster inference)

## 🚀 Setup Steps

### 1. Install on Server

```powershell
# Install Python 3.13
# Install PostgreSQL + pgvector
# Clone/copy project to server
```

### 2. Configure Environment

Create `.env` on server:
```env
# API Configuration
API_KEYS=key1,key2,key3
REQUIRE_AUTH=true
ALLOWED_ORIGINS=http://internal-server:3000,http://10.0.0.0/8

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DATABASE=ai_requests_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=strong_password_here
```

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
pip install -r api/requirements.txt
```

### 4. Run as Service

**Windows (NSSM):**
```powershell
nssm install RAGAPI "C:\Python313\python.exe" "D:\path\to\api\app.py"
nssm start RAGAPI
```

**Linux (systemd):**
```ini
[Unit]
Description=RAG API Server
After=network.target

[Service]
Type=simple
User=raguser
WorkingDirectory=/opt/rag-system
ExecStart=/usr/bin/python3 api/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5. Configure Firewall

**Windows:**
```powershell
New-NetFirewallRule -DisplayName "RAG API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

**Linux:**
```bash
ufw allow 8000/tcp
```

## 👥 User Access

### Option 1: Web Interface (Recommended)
- Build web UI that connects to API
- Users access via browser
- Internal URL: `http://internal-server:8000`

### Option 2: API Clients
- Users write their own clients
- Connect to API endpoints
- Use API keys for authentication

### Option 3: Desktop App
- Build desktop app
- Connects to API
- Works offline for UI, online for queries

## 📊 Monitoring

### Logs
- API logs: `api.log`
- Application logs: Check FastAPI output
- Database logs: PostgreSQL logs

### Health Checks
- Endpoint: `GET /api/health`
- Monitor regularly
- Alert if down

### Performance
- Track response times
- Monitor model loading
- Database query performance

## 🔄 Updates

### Updating Code
1. Stop service
2. Update code
3. Restart service
4. Model reloads on first query

### Updating Model
1. Download new model
2. Update model path in code
3. Restart service
4. Model loads on first query

## ⚠️ Important Notes

1. **First Query is Slow** - Model loads (2-5 minutes)
2. **Subsequent Queries Fast** - Model cached (5-15 seconds)
3. **Memory Usage** - Model uses 7-8GB RAM (float16)
4. **Database Connection** - Keep connection pool
5. **Backup Strategy** - Regular database backups

## 🆘 Troubleshooting

### Server Won't Start
- Check Python version (3.13)
- Check dependencies installed
- Check database connection
- Check logs

### Model Won't Load
- Check RAM (need 8GB+ free)
- Check model files exist
- Restart server (clears fragmentation)

### Users Can't Connect
- Check firewall rules
- Check API keys
- Check CORS settings
- Check network connectivity

