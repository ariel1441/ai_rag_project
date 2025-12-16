# Important Documentation - Quick Reference

**These are the essential documents you should read to understand the system.**

---

## 📚 Essential Reading Order

1. **[06_SYSTEM_FLOW_AND_ARCHITECTURE.md](06_SYSTEM_FLOW_AND_ARCHITECTURE.md)** - Start here! Overview of how everything works together
2. **[01_DATA_PREPARATION.md](01_DATA_PREPARATION.md)** - Data export, import, database setup
3. **[02_EMBEDDING_SYSTEM.md](02_EMBEDDING_SYSTEM.md)** - How embeddings are generated
4. **[03_SEARCH_SYSTEM.md](03_SEARCH_SYSTEM.md)** - How search works
5. **[04_RAG_SYSTEM.md](04_RAG_SYSTEM.md)** - How RAG generates answers
6. **[05_API_AND_FRONTEND.md](05_API_AND_FRONTEND.md)** - API, frontend, deployment
7. **[07_IMPORTANT_KNOWLEDGE.md](07_IMPORTANT_KNOWLEDGE.md)** - Key concepts and gotchas
8. **[08_CONFIGURATION_AND_TUNING.md](08_CONFIGURATION_AND_TUNING.md)** - How to adjust system behavior

---

## 📋 Document Overview

### 01_DATA_PREPARATION.md
**What it covers:**
- Exporting data from SQL Server
- Importing to PostgreSQL
- Database schema setup
- Data validation
- Everything before embedding generation

**When to read:** Before setting up a new project or understanding data flow

---

### 02_EMBEDDING_SYSTEM.md
**What it covers:**
- Field weighting (3.0x, 2.0x, 1.0x, 0.5x)
- Text chunking (512 chars, 50 overlap)
- Embedding model (sentence-transformers/all-MiniLM-L6-v2)
- Lookup tables and reference data
- How embeddings are stored

**When to read:** To understand how data becomes searchable

---

### 03_SEARCH_SYSTEM.md
**What it covers:**
- Query parser (intent detection, entity extraction)
- Semantic search (vector similarity)
- Field-specific boosting
- Similarity thresholds
- How queries are translated to results

**When to read:** To understand how search works and why results appear

---

### 04_RAG_SYSTEM.md
**What it covers:**
- RAG architecture (retrieval + generation)
- LLM model (Mistral-7B-Instruct)
- Context formatting
- Answer generation
- Model loading and quantization

**When to read:** To understand how natural language answers are generated

---

### 05_API_AND_FRONTEND.md
**What it covers:**
- FastAPI architecture
- API endpoints (search, RAG, health)
- Frontend (HTML/JavaScript)
- Deployment (server setup)
- Security considerations

**When to read:** To understand how users interact with the system

---

### 06_SYSTEM_FLOW_AND_ARCHITECTURE.md
**What it covers:**
- Complete system flow (end-to-end)
- Component architecture
- Data flow diagrams
- How components interact
- System design decisions

**When to read:** First! Get the big picture before diving into details

---

### 07_IMPORTANT_KNOWLEDGE.md
**What it covers:**
- Key concepts (embeddings, RAG, semantic search)
- Common gotchas and pitfalls
- Best practices
- Important limitations
- What to know before making changes

**When to read:** Before making significant changes or troubleshooting

---

### 08_CONFIGURATION_AND_TUNING.md
**What it covers:**
- All configurable parameters
- How to make search more/less strict
- How to adjust RAG behavior
- Performance tuning
- Making system changes

**When to read:** When you need to adjust system behavior or troubleshoot

---

## 🎯 Quick Navigation

**Want to understand...**
- **How the system works overall?** → [06_SYSTEM_FLOW_AND_ARCHITECTURE.md](06_SYSTEM_FLOW_AND_ARCHITECTURE.md)
- **How to set up data?** → [01_DATA_PREPARATION.md](01_DATA_PREPARATION.md)
- **How embeddings work?** → [02_EMBEDDING_SYSTEM.md](02_EMBEDDING_SYSTEM.md)
- **How search works?** → [03_SEARCH_SYSTEM.md](03_SEARCH_SYSTEM.md)
- **How RAG works?** → [04_RAG_SYSTEM.md](04_RAG_SYSTEM.md)
- **How to deploy?** → [05_API_AND_FRONTEND.md](05_API_AND_FRONTEND.md)
- **Important concepts?** → [07_IMPORTANT_KNOWLEDGE.md](07_IMPORTANT_KNOWLEDGE.md)
- **How to tune/adjust?** → [08_CONFIGURATION_AND_TUNING.md](08_CONFIGURATION_AND_TUNING.md)

---

**Last Updated:** Current Session  
**Status:** Organized essential documentation

