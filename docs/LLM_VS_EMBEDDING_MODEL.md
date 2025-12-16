# LLM vs Embedding Model - Complete Explanation

## 🔍 The Two Different Models

### 1. Embedding Model (80MB) - `sentence-transformers/all-MiniLM-L6-v2`

**What it does:**
- Converts text → numbers (vectors)
- Example: "פניות מאור גלילי" → `[0.23, -0.45, 0.67, ...]` (384 numbers)

**When it's used:**
1. **Building the database** (one-time, pre-computed):
   - Reads all requests from database
   - Converts each request's text → embedding
   - Stores embeddings in `request_embeddings` table
   - **This is what makes it a "vector database"**

2. **Search time** (every query):
   - Converts your query → embedding
   - Compares query embedding with stored embeddings
   - Finds similar requests

**Size:** 80MB (tiny!)
**Speed:** Very fast (<1 second per query)
**Purpose:** Similarity search only
**Always loaded:** Yes (lightweight, no problem)

**Example:**
```python
# Same model used for both!
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# 1. Building database (one-time)
request_text = "Project: אלינור | Updated By: אור גלילי"
embedding = embedding_model.encode(request_text)
# Stores [0.23, -0.45, ...] in database

# 2. Search time (every query)
query = "פניות מאור גלילי"
query_embedding = embedding_model.encode(query)
# Compares [0.23, -0.45, ...] with stored embeddings
```

---

### 2. LLM Model (7GB) - `Mistral-7B-Instruct`

**What it does:**
- Generates natural language text
- Understands context and reasoning
- Creates human-like answers

**When it's used:**
- **Only for RAG** (Type 3 queries with `use_llm=true`)
- Takes retrieved requests + query
- Generates natural language answer

**Size:** 7-8GB (huge!)
**Speed:** Slow on CPU (10-30 minutes), fast on GPU (5-15 seconds)
**Purpose:** Text generation only
**Lazy loaded:** Only when needed (saves memory)

**Example:**
```python
# LLM generates answer
prompt = """
תבסס על הבקשות הבאות:
[20 requests here]

שאלה: כמה פניות יש מאור גלילי?
"""

answer = llm_model.generate(prompt)
# Output: "נמצאו 225 פניות של אור גלילי. הפניות כוללות..."
```

---

## 📊 Key Differences

| Feature | Embedding Model | LLM Model |
|---------|----------------|-----------|
| **Size** | 80MB | 7-8GB |
| **Purpose** | Text → Numbers | Generate Text |
| **Used for** | Search (similarity) | RAG (answers) |
| **When loaded** | Always | Only when needed |
| **Speed** | <1 second | CPU: 10-30 min, GPU: 5-15 sec |
| **Memory** | ~100MB RAM | 4-8GB RAM |
| **Can skip?** | ❌ No (needed for search) | ✅ Yes (search-only works) |

---

## ✅ Answer to Your Question

**"Is the 80MB embedding model the same one used to make the DB into a vector DB?"**

**YES!** The exact same model:
- `sentence-transformers/all-MiniLM-L6-v2`
- Used to create all embeddings in database (one-time)
- Used to convert queries to embeddings (every search)
- Same model, same purpose, just used at different times

**Why this works:**
- Embeddings from same model are comparable
- If query embedding is similar to stored embedding → similar meaning
- This is how semantic search works!

---

## 🔄 How They Work Together

### Search-Only (No LLM):
```
Query: "פניות מאור גלילי"
    ↓
Embedding Model (80MB) → [0.23, -0.45, ...]
    ↓
Database Search → Top 20 requests
    ↓
Results: List of requests
```

### RAG (With LLM):
```
Query: "כמה פניות יש מאור גלילי?"
    ↓
Embedding Model (80MB) → [0.23, -0.45, ...]
    ↓
Database Search → Top 20 requests
    ↓
LLM Model (7GB) → "נמצאו 225 פניות..."
    ↓
Results: Natural language answer + list of requests
```

---

## 💡 Summary

1. **Embedding Model (80MB):**
   - Same model used for DB creation AND search
   - Converts text → numbers
   - Always loaded (lightweight)
   - Required for search

2. **LLM Model (7GB):**
   - Only used for RAG (natural language answers)
   - Generates text
   - Lazy loaded (only when needed)
   - Optional (search-only works without it)

3. **They're completely different:**
   - Different purposes
   - Different sizes
   - Different speeds
   - Used at different stages

**Bottom line:** Search uses the small embedding model (fast, always works). RAG adds the large LLM model (slow on CPU, optional).

