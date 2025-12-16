# System Flow and Architecture - Complete Guide

**Complete overview of how the entire system works together: end-to-end flow, component architecture, and design decisions**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [High-Level Flow](#high-level-flow)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [System Design Decisions](#system-design-decisions)
6. [Technology Stack](#technology-stack)

---

## Overview

**Goal:** Understand how all components work together to create a complete AI-powered request management system.

**What We Built:**
- Complete RAG system with semantic search
- Query understanding (intent detection, entity extraction)
- Field-specific search with boosting
- Natural language answer generation
- API and frontend for multi-user access

**Result:** End-to-end system from user query to natural language answer

---

## High-Level Flow

### Complete End-to-End Flow

```
User Query (Hebrew/English)
    ↓
[Query Parser] → Intent + Entities + Target Fields
    ↓
[Search] → Field-specific + Semantic + Boosting
    ↓
[Retrieval] → Top-K Relevant Requests
    ↓
[RAG] → Context Formatting + LLM Generation
    ↓
Natural Language Answer
```

### Detailed Flow

**Step 1: User Input**
- User types query in frontend or API client
- Query can be Hebrew or English
- Examples: "פניות מיניב ליבוביץ", "בקשות מסוג 4"

**Step 2: Query Parsing**
- Query parser analyzes query text
- Detects intent (person, project, type, status, general)
- Extracts entities (names, IDs, dates)
- Determines target fields to search

**Step 3: Embedding Generation**
- Embedding model converts query to vector
- 384-dimensional vector representing query meaning
- Fast process (~0.1 seconds)

**Step 4: Database Search**
- Vector similarity search (pgvector)
- Field-specific boosting (exact matches get 2.0x)
- Type/status filtering if applicable
- Result deduplication (group by request ID)

**Step 5: Total Count Calculation**
- Count all matching requests (with similarity threshold)
- Filtered queries: exact count
- Semantic queries: estimated count (with threshold)

**Step 6: Context Formatting (RAG only)**
- Format retrieved requests into context
- Query-type-specific formatting
- Optimized for LLM consumption

**Step 7: Answer Generation (RAG only)**
- Build prompt with context + query
- LLM generates natural language answer
- Extract and clean answer

**Step 8: Return Results**
- Search: List of requests + total count
- RAG: Natural language answer + list of requests

---

## Component Architecture

### Complete System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│  (Frontend: HTML/JavaScript or API Clients)               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  FastAPI Application                     │
│  (api/app.py)                                            │
│  - Routes and endpoints                                  │
│  - Error handling                                        │
│  - CORS middleware                                       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  Service Layer                           │
│  (api/services.py)                                       │
│  ┌──────────────────────┐  ┌──────────────────────┐     │
│  │  SearchService      │  │  RAGService          │     │
│  │  - Always ready     │  │  - Lazy load model   │     │
│  └──────────────────────┘  └──────────────────────┘     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  Query Parser                            │
│  (scripts/utils/query_parser.py)                        │
│  - Intent Detection (person/project/type/general)        │
│  - Entity Extraction (names, IDs)                       │
│  - Query Type (find/count/summarize/similar)             │
│  - Target Fields Determination                           │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  Search System                           │
│  (api/services.py - SearchService)                       │
│  - Embedding Generation (query → vector)                 │
│  - Vector Similarity Search (pgvector)                   │
│  - Field-Specific Boosting                               │
│  - Type/Status Filtering                                 │
│  - Result Deduplication                                  │
│  - Similarity Thresholds                                 │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  RAG System                              │
│  (scripts/core/rag_query.py)                            │
│  - Context Formatting                                    │
│  - Prompt Building                                       │
│  - LLM Generation (Mistral-7B)                          │
│  - Answer Extraction                                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  Database Layer                          │
│  (PostgreSQL + pgvector)                                │
│  - requests table (8,195 rows, 83 columns)              │
│  - request_embeddings table (36,031 chunks)             │
│  - Vector index for fast similarity search               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                  Model Layer                             │
│  - Embedding Model (sentence-transformers/all-MiniLM)   │
│    - Always loaded, ~80MB                                │
│    - Used for search                                     │
│  - LLM Model (Mistral-7B-Instruct)                      │
│    - Lazy loaded, ~4-8GB                                 │
│    - Used for RAG answer generation                      │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Search-Only Flow (Type 1)

```
User Query: "פניות מיניב ליבוביץ"
  ↓
[Query Parser]
  - Intent: person
  - Entity: "יניב ליבוביץ"
  - Target fields: updatedby, createdby, etc.
  ↓
[Embedding Model]
  - Query → Vector [0.23, -0.45, ...]
  ↓
[Database Search]
  - Vector similarity search
  - Field-specific boosting
  - Deduplication
  ↓
[Total Count]
  - Apply similarity threshold (0.5)
  - Count matching requests
  ↓
[Return Results]
  - Top 20 requests
  - Total count: ~100-400
```

### Full RAG Flow (Type 3)

```
User Query: "כמה פניות יש מיניב ליבוביץ?"
  ↓
[Query Parser]
  - Intent: person
  - Entity: "יניב ליבוביץ"
  - Query type: count
  ↓
[Search System] (same as Type 1)
  - Retrieve top 20 requests
  ↓
[Context Formatting]
  - Format 20 requests into context
  - Query-type-specific formatting
  ↓
[Prompt Building]
  - Build prompt with context + query
  - Use Mistral's chat template
  ↓
[LLM Generation]
  - Generate answer (if model not loaded, load first)
  - Temperature: 0.7, Max length: 500
  ↓
[Answer Extraction]
  - Extract clean answer from LLM output
  ↓
[Return Results]
  - Natural language answer
  - List of requests
  - Total count
```

---

## System Design Decisions

### Why This Architecture?

**1. Two Models (Embedding + LLM):**
- **Embedding model:** Fast, lightweight, perfect for search
- **LLM model:** Slow, heavy, perfect for answer generation
- **RAG combines both:** Fast search + smart answers

**2. Query Parser (No AI):**
- **Pattern matching:** Fast, deterministic
- **Configurable:** Easy to adjust for different clients
- **No model needed:** Works immediately

**3. Field Weighting:**
- **Emphasizes important fields:** Better search results
- **Configurable weights:** Easy to adjust
- **Standard practice:** Industry best practice

**4. Chunking (512 chars, 50 overlap):**
- **Standard size:** Common practice in industry
- **Overlap prevents lost context:** Better continuity
- **Multiple chunks per request:** Better granularity

**5. Two RAG Versions:**
- **High-end:** Best performance (4-bit, GPU)
- **Compatible:** Works everywhere (float16, CPU)
- **Choose based on system:** Flexible deployment

**6. Lazy Loading:**
- **Model loads on first use:** Saves RAM when not using RAG
- **Stays in memory:** Fast subsequent queries
- **Shared by all users:** Efficient for server deployment

**7. Similarity Thresholds:**
- **Filters noise:** More accurate total counts
- **Different thresholds:** Person/project (0.5) vs general (0.4)
- **No threshold for filtered queries:** Exact counts

---

## Technology Stack

### Core Technologies

**Database:**
- PostgreSQL 18
- pgvector extension (vector similarity search)

**Embedding:**
- sentence-transformers/all-MiniLM-L6-v2
- 384-dimensional vectors

**LLM:**
- Mistral-7B-Instruct-v0.2
- 4-bit quantization or float16

**API:**
- FastAPI (Python web framework)
- Uvicorn (ASGI server)

**Frontend:**
- HTML + JavaScript (vanilla)
- Served from FastAPI

**Language:**
- Python 3.13

**Platform:**
- Windows (development)
- Linux/Windows Server (production)

---

## Component Interactions

### How Components Work Together

**1. Query Parser → Search:**
- Parser determines intent and target fields
- Search uses this to focus on relevant fields
- Boosting uses target fields for exact match detection

**2. Search → RAG:**
- RAG uses search to retrieve relevant requests
- Better search = better RAG results
- Search doesn't need to be perfect - RAG can help interpret

**3. Embedding Model → Search:**
- Embedding model converts query to vector
- Search uses vector for similarity comparison
- Same model used for data embeddings and query embeddings

**4. LLM → RAG:**
- RAG formats context for LLM
- LLM generates answer from context
- LLM only used when `use_llm=true`

**5. Database → Everything:**
- All components read from database
- Embeddings stored in database
- Search queries database
- RAG retrieves from database

---

## Summary

**Complete System:**
1. User query → Query parser → Intent + entities
2. Query → Embedding model → Vector
3. Vector → Database search → Similar requests
4. Requests → Context formatting → LLM → Answer
5. Answer + Requests → User

**Key Points:**
- Two models (embedding for search, LLM for answers)
- Query parser understands Hebrew patterns
- Field-specific search with boosting
- Similarity thresholds for accurate counts
- Lazy loading saves RAM
- One server, multiple users

**Key Files:**
- `COMPLETE_PROJECT_GUIDE.md` - Main project guide
- `api/app.py` - FastAPI application
- `api/services.py` - Service layer
- `scripts/utils/query_parser.py` - Query parsing
- `scripts/core/rag_query.py` - RAG system

---

**Last Updated:** Current Session  
**Status:** Complete system architecture documented

