# Complete Guide to Configurable Parameters

**All settings and parameters you can adjust to change system behavior**

---

## 📋 Table of Contents

1. [Embedding Settings](#1-embedding-settings)
2. [Text Processing Settings](#2-text-processing-settings)
3. [Search Settings](#3-search-settings)
4. [Query Parser Settings](#4-query-parser-settings)
5. [RAG Settings](#5-rag-settings)
6. [Model Settings](#6-model-settings)
7. [API Settings](#7-api-settings)

---

## 1. Embedding Settings

### 1.1 Embedding Model

**Location:** `scripts/core/generate_embeddings.py`, `scripts/core/rag_query.py`, `api/services.py`

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
# In generate_embeddings.py, rag_query.py, or api/services.py
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")  # Better quality, slower
# OR
model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")  # Better multilingual
```

**Alternatives:**
- `all-mpnet-base-v2`: Better quality (768 dims), slower
- `paraphrase-multilingual-mpnet-base-v2`: Better multilingual, larger
- `all-MiniLM-L6-v2`: Current (best balance) ✅

**Impact:**
- **Higher quality model:** Better search accuracy, slower, more RAM
- **Current model:** Fast, good quality, balanced ✅

---

## 2. Text Processing Settings

### 2.1 Chunk Size (`max_chunk_size`)

**Location:** `scripts/utils/text_processing.py` (line 194)

**Current Value:**
```python
max_chunk_size = 512  # characters
```

**What it does:**
- Maximum size of each text chunk before splitting
- Standard practice: 512 characters

**How to change:**
```python
# In text_processing.py, chunk_text() function
def chunk_text(text: str, max_chunk_size: int = 512, overlap: int = 50):
    # Change default from 512 to your desired value
```

**Recommended values:**
- **256:** Smaller chunks, more granular, more chunks per request
- **512:** ✅ **Current (standard practice)**
- **1024:** Larger chunks, fewer chunks, may lose context boundaries

**Impact:**
- **Smaller:** More chunks, better granularity, more database rows
- **Larger:** Fewer chunks, may miss context at boundaries

**Code locations:**
- `scripts/utils/text_processing.py:194`
- `scripts/core/generate_embeddings.py:135` (calls `chunk_text(combined_text, max_chunk_size=512, overlap=50)`)

---

### 2.2 Chunk Overlap

**Location:** `scripts/utils/text_processing.py` (line 194)

**Current Value:**
```python
overlap = 50  # characters (~10% of 512)
```

**What it does:**
- Number of characters to overlap between chunks
- Prevents context loss at boundaries

**How to change:**
```python
# In text_processing.py, chunk_text() function
def chunk_text(text: str, max_chunk_size: int = 512, overlap: int = 50):
    # Change default from 50 to your desired value
```

**Recommended values:**
- **25-50:** ✅ **Current (10-20% overlap, standard practice)**
- **100:** More overlap, ensures no context loss, more chunks
- **0:** No overlap, may lose context at boundaries

**Impact:**
- **More overlap:** Better context preservation, more chunks
- **Less overlap:** Fewer chunks, may lose context

**Code locations:**
- `scripts/utils/text_processing.py:194`
- `scripts/core/generate_embeddings.py:135`

---

### 2.3 Max Chunks Per Request

**Location:** `scripts/utils/text_processing.py` (line 214)

**Current Value:**
```python
max_chunks = 100  # Safety limit
```

**What it does:**
- Maximum number of chunks per request
- Safety limit to prevent memory issues

**How to change:**
```python
# In text_processing.py, chunk_text() function
max_chunks = 100  # Change to your desired limit
```

**Recommended values:**
- **50:** Stricter limit, fewer chunks
- **100:** ✅ **Current (good balance)**
- **200:** More chunks allowed, more memory usage

**Impact:**
- **Lower:** Fewer chunks, may truncate very long requests
- **Higher:** More chunks, more memory usage

---

### 2.4 Field Weighting

**Location:** `scripts/utils/text_processing.py` (function `combine_text_fields_weighted`)

**Current Values:**
- **Weight 3.0x (Repeat 3 times):** Critical fields (projectname, updatedby, projectdesc, areadesc, remarks, requesttypeid)
- **Weight 2.0x (Repeat 2 times):** Important fields (createdby, responsibleemployeename, contact names, etc.)
- **Weight 1.0x (Include once):** Supporting fields (descriptions, dates, etc.)
- **Weight 0.5x (Include once):** Specific fields (booleans, coordinates)

**What it does:**
- Determines how many times each field appears in the combined text
- More repetitions = higher importance in search

**How to change:**
```python
# In text_processing.py, combine_text_fields_weighted() function

# Change weight 3.0x fields (repeat 3 times)
for _ in range(3):  # Change 3 to 2 or 4
    fields.append(f"{field_label}: {value}")

# Change weight 2.0x fields (repeat 2 times)
for _ in range(2):  # Change 2 to 1 or 3
    fields.append(f"{field_label}: {value}")
```

**Impact:**
- **More repetitions:** Field has more weight in search, appears more often
- **Fewer repetitions:** Field has less weight, appears less often

**To add/remove fields:**
- Edit the field lists in `combine_text_fields_weighted()`:
  - `critical_fields` (weight 3.0x)
  - `important_fields` (weight 2.0x)
  - `supporting_fields` (weight 1.0x)
  - `boolean_fields` (weight 0.5x)

---

## 3. Search Settings

### 3.1 Top-K (Number of Results)

**Location:** `api/services.py:75`, `scripts/core/rag_query.py:391`, `scripts/core/search.py`

**Current Value:**
```python
top_k = 20  # Default
```

**What it does:**
- Number of requests to return in search results
- Default: 20 requests

**How to change:**
```python
# In API call
POST /api/search
{
    "query": "פניות מיניב ליבוביץ",
    "top_k": 30  # Change from 20 to your desired value
}

# In code
results, count = search_service.search(query, top_k=30)  # Change from 20
```

**Recommended values:**
- **5-10:** Fewer results, faster, less context
- **20:** ✅ **Current (good balance)**
- **30-50:** More results, slower, more context

**Impact:**
- **More results:** Better coverage, more context, slower
- **Fewer results:** Faster, less context, might miss relevant requests

**Code locations:**
- `api/services.py:75` - `def search(self, query: str, top_k: int = 20)`
- `scripts/core/rag_query.py:391` - `def retrieve_requests(self, query: str, top_k: int = 20)`
- `api/app.py` - API endpoint accepts `top_k` in request

---

### 3.2 Similarity Threshold (For Count Query)

**Location:** `api/services.py:187-193`

**Current Values:**
```python
# Person/Project queries
similarity_threshold = 0.5  # 50% similarity

# General queries
similarity_threshold = 0.4  # 40% similarity

# Filtered queries (type/status)
# No threshold - uses filter only
```

**What it does:**
- Minimum similarity score to include in total count
- Filters out low-relevance results from count

**How to change:**
```python
# In api/services.py, search() function
if intent in ['person', 'project']:
    similarity_threshold = 0.5  # Change to 0.4 (more results) or 0.6 (fewer results)
else:
    similarity_threshold = 0.4  # Change to 0.3 (more results) or 0.5 (fewer results)
```

**Recommended values:**
- **0.3 (30%):** More lenient, includes more results, higher counts
- **0.4 (40%):** ✅ **Current for general queries**
- **0.5 (50%):** ✅ **Current for person/project queries**
- **0.6 (60%):** Stricter, fewer results, lower counts

**Impact:**
- **Lower threshold:** More results counted, higher total count
- **Higher threshold:** Fewer results counted, lower total count (more accurate)

**Note:** This only affects the **count display**, not the actual search results.

---

### 3.3 Search Limit Multiplier

**Location:** `api/services.py:221`, `scripts/core/rag_query.py:509`

**Current Value:**
```python
LIMIT {top_k * 3}  # Fetch 3x more chunks than needed
```

**What it does:**
- Fetches more chunks than needed, then deduplicates by request ID
- Ensures we get enough unique requests

**How to change:**
```python
# In api/services.py, search() function
LIMIT {top_k * 3}  # Change 3 to 2 (fewer chunks) or 5 (more chunks)
```

**Recommended values:**
- **2x:** Fewer chunks fetched, faster, might miss some requests
- **3x:** ✅ **Current (good balance)**
- **5x:** More chunks fetched, slower, ensures all requests found

**Impact:**
- **Lower multiplier:** Faster, might miss some requests
- **Higher multiplier:** Slower, ensures all requests found

---

### 3.4 Boost Values (Field-Specific Search)

**Location:** `api/services.py:150-153`, `scripts/core/search.py:207-210`, `config/search_config.json:66-71`

**Current Values:**
```python
# Exact match in target field
boost = 2.0  # 2x boost

# Entity appears anywhere in chunk
boost = 1.5  # 1.5x boost

# Semantic match only
boost = 1.0  # No boost
```

**What it does:**
- Multiplies similarity score based on match type
- Higher boost = higher ranking

**How to change:**
```python
# In api/services.py, search() function
# Exact match in target field
boost_cases.append(f"WHEN e.text_chunk LIKE '%{label}: %{entity_escaped}%' THEN 2.0")
# Change 2.0 to 2.5 (more boost) or 1.5 (less boost)

# Entity in chunk
boost_cases.append(f"WHEN e.text_chunk LIKE '%{entity_escaped}%' THEN 1.5")
# Change 1.5 to 2.0 (more boost) or 1.2 (less boost)
```

**OR in config file:**
```json
// config/search_config.json
{
  "boost_rules": {
    "exact_match_in_target_field": 2.0,  // Change this
    "exact_match_in_other_field": 1.5,   // Change this
    "semantic_match": 1.0,               // Change this
    "keyword_match": 1.2                  // Change this
  }
}
```

**Recommended values:**
- **Exact match:** 2.0-3.0 (higher = more emphasis on exact matches)
- **Entity in chunk:** 1.5-2.0 (higher = more emphasis on keyword matches)
- **Semantic match:** 1.0 (baseline)

**Impact:**
- **Higher boost:** Exact matches rank higher, more precise results
- **Lower boost:** Semantic matches rank higher, more flexible results

---

## 4. Query Parser Settings

### 4.1 Query Patterns

**Location:** `config/search_config.json:2-33`

**Current Values:**
```json
{
  "query_patterns": {
    "person_queries": {
      "patterns": ["מא", "של", "על ידי", "מאת", "מ-"],
      "target_fields": ["updatedby", "createdby", "responsibleemployeename", ...]
    },
    "project_queries": {
      "patterns": ["פרויקט", "project", "שם פרויקט"],
      "target_fields": ["projectname", "projectdesc"]
    },
    // ... more patterns
  }
}
```

**What it does:**
- Defines patterns that trigger specific intent detection
- Determines which fields to search

**How to change:**
```json
// In config/search_config.json
{
  "query_patterns": {
    "person_queries": {
      "patterns": ["מא", "של", "על ידי", "מאת", "מ-", "NEW_PATTERN"],  // Add patterns
      "target_fields": ["updatedby", "createdby", "NEW_FIELD"]  // Add fields
    }
  }
}
```

**Impact:**
- **Add patterns:** More queries detected as that intent
- **Add fields:** More fields searched for that intent

---

### 4.2 Field Mappings

**Location:** `config/search_config.json:34-47`

**Current Values:**
```json
{
  "field_mappings": {
    "מסוג": "requesttypeid",
    "סטטוס": "requeststatusid",
    "פרויקט": "projectname",
    // ... more mappings
  }
}
```

**What it does:**
- Maps Hebrew keywords to database field names
- Used for entity extraction

**How to change:**
```json
// In config/search_config.json
{
  "field_mappings": {
    "מסוג": "requesttypeid",
    "NEW_HEBREW_WORD": "field_name"  // Add new mappings
  }
}
```

**Impact:**
- **Add mappings:** More keywords recognized, better entity extraction

---

### 4.3 Query Types

**Location:** `config/search_config.json:48-65`

**Current Values:**
```json
{
  "query_types": {
    "find": {
      "patterns": ["תביא", "הראה", "מצא", "show", "find", "bring"]
    },
    "count": {
      "patterns": ["כמה", "מספר", "count", "how many"]
    },
    // ... more types
  }
}
```

**What it does:**
- Defines patterns for different query types (find, count, summarize, similar)
- Used for prompt generation in RAG

**How to change:**
```json
// In config/search_config.json
{
  "query_types": {
    "find": {
      "patterns": ["תביא", "הראה", "מצא", "NEW_PATTERN"]  // Add patterns
    }
  }
}
```

**Impact:**
- **Add patterns:** More queries detected as that type, different prompts used

---

## 5. RAG Settings

### 5.1 LLM Model Path

**Location:** `scripts/core/rag_query.py:92-99`, `scripts/core/rag_query_high_end.py`

**Current Value:**
```python
model_path = "D:/ai_learning/train_ai_tamar_request/models/llm/mistral-7b-instruct"
```

**What it does:**
- Path to the LLM model directory
- Used for loading Mistral-7B-Instruct

**How to change:**
```python
# In rag_query.py, __init__() method
rag = RAGSystem(model_path="path/to/your/model")
```

**Impact:**
- **Different model:** Different quality, size, speed

---

### 5.2 Model Quantization

**Location:** `scripts/core/rag_query.py` (load_model method)

**Current Behavior:**
- **Compatible version:** Skips 4-bit on Windows CPU, uses float16 (~7-8GB)
- **High-end version:** Attempts 4-bit (~4GB), falls back to float16

**What it does:**
- Reduces model size and RAM usage
- 4-bit: ~4GB RAM, 95-98% quality
- float16: ~7-8GB RAM, 100% quality

**How to change:**
```python
# In rag_query.py, load_model() method
# To force 4-bit (if available):
load_in_4bit = True

# To force float16:
load_in_4bit = False
torch_dtype = torch.float16
```

**Impact:**
- **4-bit:** Less RAM, slightly lower quality, faster loading
- **float16:** More RAM, full quality, slower loading

---

### 5.3 Generation Parameters

**Location:** `scripts/core/rag_query.py:697-748`

**Current Values:**
```python
max_length = 500  # Maximum answer length
max_new_tokens = 500  # Maximum new tokens to generate
temperature = 0.7  # Creativity (0.0 = deterministic, 1.0 = creative)
do_sample = True  # Enable sampling
```

**What it does:**
- Controls LLM answer generation
- `temperature`: Higher = more creative, lower = more deterministic
- `max_length`: Maximum answer length in characters
- `max_new_tokens`: Maximum tokens to generate

**How to change:**
```python
# In rag_query.py, generate_answer() method
def generate_answer(self, user_content: str, max_length: int = 500):
    # Change default max_length
    # ...
    outputs = self.model.generate(
        inputs["input_ids"],
        max_new_tokens=max_length,  # Change this
        temperature=0.7,  # Change this (0.0-1.0)
        do_sample=True,  # Change to False for deterministic
    )
```

**Recommended values:**
- **max_length:** 300-1000 (shorter = faster, longer = more detailed)
- **temperature:** 0.5-0.9 (0.5 = more focused, 0.9 = more creative)
- **do_sample:** True (enables temperature), False (deterministic)

**Impact:**
- **Higher temperature:** More creative answers, less consistent
- **Lower temperature:** More focused answers, more consistent
- **Longer max_length:** More detailed answers, slower

---

### 5.4 Context Formatting

**Location:** `scripts/core/rag_query.py:600-650` (format_context method)

**Current Behavior:**
- Formats retrieved requests into context for LLM
- Includes: Request ID, Project, Updated By, Type, Status, Description

**What it does:**
- Prepares context from retrieved requests
- Determines what information to include

**How to change:**
```python
# In rag_query.py, format_context() method
def format_context(self, requests: List[Dict]) -> str:
    # Modify which fields are included
    context_parts = [
        f"Request ID: {req['requestid']}",
        f"Project: {req.get('projectname', 'N/A')}",
        # Add or remove fields here
    ]
```

**Impact:**
- **More fields:** More context, better answers, longer prompts
- **Fewer fields:** Less context, faster, shorter prompts

---

### 5.5 Prompt Templates

**Location:** `scripts/core/rag_query.py:650-690` (build_prompt method)

**Current Behavior:**
- Uses Mistral's chat template format
- Different prompts for different query types (count, find, summarize)

**What it does:**
- Formats the prompt sent to LLM
- Includes instructions, context, and query

**How to change:**
```python
# In rag_query.py, build_prompt() method
def build_prompt(self, query: str, context: str, query_type: str = "find") -> str:
    # Modify prompt templates here
    if query_type == "count":
        system_prompt = "You are a helpful assistant..."  # Change this
    # ...
```

**Impact:**
- **Better prompts:** Better answers, more accurate
- **Worse prompts:** Less accurate answers

---

## 6. Model Settings

### 6.1 Embedding Model

**Location:** Multiple files (see Embedding Settings section)

**Current:** `sentence-transformers/all-MiniLM-L6-v2`

**Alternatives:**
- `all-mpnet-base-v2`: Better quality, slower
- `paraphrase-multilingual-mpnet-base-v2`: Better multilingual

---

### 6.2 LLM Model

**Location:** `scripts/core/rag_query.py`, `scripts/core/rag_query_high_end.py`

**Current:** `mistralai/Mistral-7B-Instruct-v0.2`

**Alternatives:**
- `mistralai/Mistral-7B-Instruct-v0.1`: Older version
- `meta-llama/Llama-2-7b-chat-hf`: Different model (requires approval)
- `microsoft/phi-2`: Smaller model, faster

**How to change:**
```python
# Download new model, then update model_path
rag = RAGSystem(model_path="path/to/new/model")
```

---

## 7. API Settings

### 7.1 API Port

**Location:** `api/start_server.ps1`, `api/app.py`

**Current Value:**
```python
uvicorn.run(app, host="127.0.0.1", port=8000)
```

**How to change:**
```python
# In start_server.ps1 or app.py
uvicorn.run(app, host="127.0.0.1", port=8080)  # Change port
```

---

### 7.2 API Timeout

**Location:** `api/app.py` (if set)

**Current:** No explicit timeout (uses default)

**How to add:**
```python
# In api/app.py
@app.post("/api/search")
async def search_requests(request: SearchRequest, timeout: int = 30):
    # Add timeout logic
```

---

### 7.3 CORS Settings

**Location:** `api/app.py`

**Current Value:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**How to change:**
```python
# In api/app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],  # Specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

**Impact:**
- **Allow all origins:** Easy for development, less secure
- **Specific origins:** More secure, requires configuration

---

## 📊 Summary Table

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

## 🎯 Quick Reference: Making System More/Less Strict

### To Make Search More Strict (Fewer Results):
1. **Increase similarity threshold:** `0.5 → 0.6` (person/project), `0.4 → 0.5` (general)
2. **Increase boost values:** `2.0 → 2.5` (exact match), `1.5 → 2.0` (entity in chunk)
3. **Decrease top_k:** `20 → 10` (fewer results returned)

### To Make Search Less Strict (More Results):
1. **Decrease similarity threshold:** `0.5 → 0.4` (person/project), `0.4 → 0.3` (general)
2. **Decrease boost values:** `2.0 → 1.5` (exact match), `1.5 → 1.2` (entity in chunk)
3. **Increase top_k:** `20 → 30` (more results returned)

### To Make RAG More Focused:
1. **Decrease temperature:** `0.7 → 0.5`
2. **Decrease max_length:** `500 → 300`
3. **Set do_sample to False:** More deterministic

### To Make RAG More Creative:
1. **Increase temperature:** `0.7 → 0.9`
2. **Increase max_length:** `500 → 800`
3. **Keep do_sample True:** More variation

---

## 📝 Notes

- **After changing parameters:** Restart the server/script to apply changes
- **Test changes:** Run test queries to verify behavior
- **Document changes:** Note what you changed and why
- **Backup configs:** Keep original config files before making changes

---

**Last Updated:** Current Session  
**Status:** Complete guide to all configurable parameters

