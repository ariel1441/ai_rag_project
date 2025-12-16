# Configuration and Tuning - Complete Guide

**All configurable parameters and settings you can adjust to change system behavior**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Embedding Settings](#embedding-settings)
3. [Text Processing Settings](#text-processing-settings)
4. [Search Settings](#search-settings)
5. [Query Parser Settings](#query-parser-settings)
6. [RAG Settings](#rag-settings)
7. [API Settings](#api-settings)
8. [Making System More/Less Strict](#making-system-moreless-strict)
9. [Summary Table](#summary-table)

---

## Overview

**Goal:** Understand all parameters you can adjust to tune system behavior.

**What You Can Adjust:**
- Embedding model selection
- Field weights and chunking
- Search thresholds and boosting
- Query parser patterns
- RAG generation parameters
- API settings

**Result:** Full control over system behavior and performance

---

## Embedding Settings

### Embedding Model

**Location:** `scripts/core/generate_embeddings.py`, `api/services.py`

**Current Value:**
```python
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
```

**What it does:**
- Converts text to 384-dimensional vectors
- Used for semantic search
- Fast and efficient (~500MB)

**How to change:**
```python
# Better quality, slower
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")  # 768 dims

# Better multilingual
model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
```

**Alternatives:**
- `all-mpnet-base-v2`: Better quality (768 dims), slower
- `paraphrase-multilingual-mpnet-base-v2`: Better multilingual, larger
- `all-MiniLM-L6-v2`: Current (best balance) ✅

**Impact:**
- **Higher quality model:** Better search accuracy, slower, more RAM
- **Current model:** Fast, good quality, balanced ✅

**After change:** Regenerate embeddings!

---

## Text Processing Settings

### Chunk Size

**Location:** `scripts/utils/text_processing.py:194`

**Current Value:**
```python
max_chunk_size = 512  # characters
```

**What it does:**
- Maximum size of each text chunk before splitting
- Standard practice: 512 characters

**How to change:**
```python
chunks = chunk_text(text, max_chunk_size=512, overlap=50)
# Change 512 to your desired value
```

**Recommended values:**
- **256:** Smaller chunks, more granular, more chunks per request
- **512:** ✅ **Current (standard practice)**
- **1024:** Larger chunks, fewer chunks, may lose context boundaries

**Impact:**
- **Smaller:** More chunks, better granularity, more database rows
- **Larger:** Fewer chunks, may miss context at boundaries

**After change:** Regenerate embeddings!

---

### Chunk Overlap

**Location:** `scripts/utils/text_processing.py:194`

**Current Value:**
```python
overlap = 50  # characters (~10% of 512)
```

**What it does:**
- Overlap between chunks to prevent lost context
- ~10% overlap is standard practice

**How to change:**
```python
chunks = chunk_text(text, max_chunk_size=512, overlap=50)
# Change 50 to your desired value
```

**Recommended values:**
- **25:** Less overlap, fewer chunks
- **50:** ✅ **Current (~10% overlap)**
- **100:** More overlap, better context, more chunks

**Impact:**
- **More overlap:** Better context, more chunks
- **Less overlap:** Fewer chunks, may lose context at boundaries

**After change:** Regenerate embeddings!

---

### Field Weights

**Location:** `scripts/utils/text_processing.py` - `combine_text_fields_weighted()` function

**Current Weights:**
- Weight 3.0x: 6 fields (ProjectName, UpdatedBy, ProjectDesc, AreaDesc, Remarks, RequestTypeId)
- Weight 2.0x: 10 fields (CreatedBy, RequestStatusId, ContactFirstName, etc.)
- Weight 1.0x: 12 fields (ResponsibleOrgEntityName, ContactPhone, etc.)
- Weight 0.5x: 16 fields (booleans, coordinates, flags)

**How to change:**
- Modify weight categories in `combine_text_fields_weighted()`
- Add/remove fields from each category
- Adjust repetition counts

**Impact:**
- **Higher weight:** More emphasis on field, better search for that field
- **Lower weight:** Less emphasis, may miss relevant results

**After change:** Regenerate embeddings!

---

## Search Settings

### Top-K Results

**Location:** `api/services.py:75`

**Current Value:**
```python
def search(self, query: str, top_k: int = 20):
```

**What it does:**
- Number of results to return
- Default: 20

**How to change:**
```python
# In API call
{"query": "...", "top_k": 30}

# Or change default in services.py
def search(self, query: str, top_k: int = 30):
```

**Impact:**
- **More results:** Better coverage, slower
- **Fewer results:** Faster, may miss relevant items

---

### Similarity Thresholds

**Location:** `api/services.py:191-193`

**Current Values:**
```python
if intent in ['person', 'project']:
    similarity_threshold = 0.5  # 50% for person/project
else:
    similarity_threshold = 0.4  # 40% for general semantic queries
```

**What it does:**
- Filters low-relevance results from total count
- Applied to COUNT query only

**How to change:**
```python
# Make more strict
similarity_threshold = 0.6  # Higher = fewer results

# Make less strict
similarity_threshold = 0.3  # Lower = more results
```

**Impact:**
- **Higher threshold:** Fewer results, more accurate
- **Lower threshold:** More results, may include noise

---

### Boost Values

**Location:** `api/services.py:150, 153`

**Current Values:**
```python
# Exact match in target field
boost = 2.0

# Entity in chunk
boost = 1.5

# Semantic similarity
boost = 1.0
```

**What it does:**
- Ranks exact matches higher than semantic matches

**How to change:**
```python
# More emphasis on exact matches
boost = 2.5  # Instead of 2.0

# Less emphasis on exact matches
boost = 1.5  # Instead of 2.0
```

**Impact:**
- **Higher boost:** More emphasis on exact matches
- **Lower boost:** More emphasis on semantic matches

---

### Search Limit Multiplier

**Location:** `api/services.py:221`

**Current Value:**
```python
search_limit = top_k * 3  # Fetch 60 chunks for top 20 results
```

**What it does:**
- Multiplies top_k to fetch more chunks for deduplication
- Accounts for multiple chunks per request

**How to change:**
```python
search_limit = top_k * 3  # Change multiplier
```

**Impact:**
- **Higher multiplier:** More chunks fetched, slower, better deduplication
- **Lower multiplier:** Fewer chunks fetched, faster, may miss results

---

## Query Parser Settings

### Query Patterns

**Location:** `config/search_config.json`

**Current Patterns:**
```json
{
  "query_patterns": {
    "person_queries": {
      "patterns": ["מא", "של", "על ידי", "מאת", "מ-"],
      "target_fields": ["updatedby", "createdby", ...]
    },
    "project_queries": {
      "patterns": ["פרויקט", "project", "שם פרויקט"],
      "target_fields": ["projectname", "projectdesc"]
    }
  }
}
```

**How to change:**
- Edit `config/search_config.json`
- Add/remove patterns
- Change target fields

**Impact:**
- **More patterns:** Better query understanding
- **Fewer patterns:** May miss some query types

---

### Field Mappings

**Location:** `config/search_config.json`

**Current Mappings:**
```json
{
  "field_mappings": {
    "מסוג": "requesttypeid",
    "סטטוס": "requeststatusid",
    "פרויקט": "projectname"
  }
}
```

**How to change:**
- Edit `config/search_config.json`
- Add/remove mappings
- Map Hebrew words to database fields

**Impact:**
- **More mappings:** Better query understanding
- **Fewer mappings:** May miss some queries

---

## RAG Settings

### Model Path

**Location:** `scripts/core/rag_query.py`

**Current Value:**
```python
model_path = "models/llm/mistral-7b-instruct"
```

**How to change:**
```python
rag = RAGSystem(model_path="path/to/your/model")
```

**Impact:**
- Different model = different quality/behavior
- Must be compatible format (HuggingFace)

---

### Retrieval Settings

**Top-K:**
- Default: 20 requests
- How to change: `rag.query(query, top_k=30)`

**Impact:**
- More requests = better context, slower generation
- Fewer requests = faster, may miss relevant info

---

### Generation Parameters

**Location:** `scripts/core/rag_query.py` - `generate_answer()` function

**Current Settings:**
```python
outputs = model.generate(
    inputs,
    max_length=500,      # Max tokens
    temperature=0.7,     # Creativity/accuracy balance
    do_sample=True        # Allow variation
)
```

**How to change:**
```python
# More focused
max_length=300
temperature=0.5
do_sample=False

# More creative
max_length=800
temperature=0.9
do_sample=True
```

**Impact:**
- **Higher temperature:** More creative, less focused
- **Lower temperature:** More focused, less creative
- **Longer max_length:** More detailed, slower
- **Shorter max_length:** Less detailed, faster

---

## API Settings

### Port

**Location:** `api/start_server.ps1`, `api/app.py`

**Current:** Port 8000

**How to change:**
```powershell
# In start_server.ps1
uvicorn api.app:app --host 127.0.0.1 --port 8000
# Change 8000 to your desired port
```

---

### CORS Settings

**Location:** `api/app.py`

**Current:**
```python
allow_origins=["*"]  # Allows all origins (development)
```

**For production:**
```python
allow_origins=["http://internal-server:3000", "http://10.0.0.0/8"]
```

**Impact:**
- **Allow all origins:** Easy for development, less secure
- **Specific origins:** More secure, requires configuration

---

### API Keys

**Location:** `.env`

**Current:**
```env
API_KEYS=key1,key2,key3
REQUIRE_AUTH=false
```

**For production:**
```env
API_KEYS=strong_key_1,strong_key_2
REQUIRE_AUTH=true
```

---

## Making System More/Less Strict

### To Make Search More Strict (Fewer Results):

1. **Increase similarity threshold:**
   - `0.5 → 0.6` (person/project)
   - `0.4 → 0.5` (general)

2. **Increase boost values:**
   - `2.0 → 2.5` (exact match)
   - `1.5 → 2.0` (entity in chunk)

3. **Decrease top_k:**
   - `20 → 10` (fewer results returned)

---

### To Make Search Less Strict (More Results):

1. **Decrease similarity threshold:**
   - `0.5 → 0.4` (person/project)
   - `0.4 → 0.3` (general)

2. **Decrease boost values:**
   - `2.0 → 1.5` (exact match)
   - `1.5 → 1.2` (entity in chunk)

3. **Increase top_k:**
   - `20 → 30` (more results returned)

---

### To Make RAG More Focused:

1. **Decrease temperature:** `0.7 → 0.5`
2. **Decrease max_length:** `500 → 300`
3. **Set do_sample to False:** More deterministic

---

### To Make RAG More Creative:

1. **Increase temperature:** `0.7 → 0.9`
2. **Increase max_length:** `500 → 800`
3. **Keep do_sample True:** More variation

---

## Summary Table

| Parameter | Location | Current Value | Impact of Change |
|-----------|----------|---------------|------------------|
| **Chunk Size** | `text_processing.py:194` | 512 | Smaller = more chunks, larger = fewer chunks |
| **Chunk Overlap** | `text_processing.py:194` | 50 | More = better context, less = fewer chunks |
| **Top-K** | `api/services.py:75` | 20 | More = better coverage, less = faster |
| **Similarity Threshold (Person)** | `api/services.py:191` | 0.5 | Higher = stricter, lower = more lenient |
| **Similarity Threshold (General)** | `api/services.py:193` | 0.4 | Higher = stricter, lower = more lenient |
| **Boost (Exact Match)** | `api/services.py:150` | 2.0 | Higher = more emphasis on exact matches |
| **Boost (Entity in Chunk)** | `api/services.py:153` | 1.5 | Higher = more emphasis on keyword matches |
| **Search Limit Multiplier** | `api/services.py:221` | 3x | Higher = more chunks fetched, slower |
| **Max Answer Length** | `rag_query.py:697` | 500 | Longer = more detailed, slower |
| **Temperature** | `rag_query.py:747` | 0.7 | Higher = more creative, lower = more focused |

---

## Notes

- **After changing parameters:** Restart the server/script to apply changes
- **Test changes:** Run test queries to verify behavior
- **Document changes:** Note what you changed and why
- **Backup configs:** Keep original config files before making changes
- **Regenerate embeddings:** After changing field weights or chunking

---

## Quick Reference

**For detailed information:**
- See `CONFIGURABLE_PARAMETERS_GUIDE.md` - Complete parameter reference
- See component-specific docs (01-05) - Detailed explanations
- See code comments - Implementation details

---

**Last Updated:** Current Session  
**Status:** Complete parameter reference

