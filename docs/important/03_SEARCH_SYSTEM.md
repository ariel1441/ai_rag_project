# Search System - Complete Guide

**Everything about how search works: query parsing, semantic search, boosting, and similarity thresholds**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Query Parser](#query-parser)
3. [Semantic Search](#semantic-search)
4. [Field-Specific Boosting](#field-specific-boosting)
5. [Similarity Thresholds](#similarity-thresholds)
6. [Total Count Calculation](#total-count-calculation)
7. [Complete Search Flow](#complete-search-flow)
8. [Configuration](#configuration)

---

## Overview

**Goal:** Find relevant requests using semantic similarity and field-specific logic.

**What We Do:**
- Parse user query to understand intent
- Convert query to embedding vector
- Search database using vector similarity
- Boost exact matches in target fields
- Apply similarity thresholds for accurate counts
- Return top-k results with total count

**Result:** Fast, accurate search that understands Hebrew queries and finds requests by meaning

---

## Query Parser

### Purpose

**Understands user intent** without using AI models - just pattern matching and rules.

**What it does:**
1. **Intent Detection:** person, project, type, status, general
2. **Entity Extraction:** names, IDs, dates
3. **Target Fields:** Determines which fields to search
4. **Query Type:** find, count, summarize, similar

### How It Works

**Example: "פניות מיניב ליבוביץ"**

1. **Pattern Detection:**
   - Finds "מ" (from) → indicates person query
   - Pattern "מ" is in `person_patterns` config

2. **Intent Detection:**
   - Detects intent = `person` (because of "מ" pattern)

3. **Entity Extraction:**
   - Extracts person name: "יניב ליבוביץ"
   - Handles Hebrew prefixes correctly:
     - "מיניב" → removes "מ" → "יניב ליבוביץ"
     - Handles "א" character correctly

4. **Target Fields:**
   - Sets target_fields = `['updatedby', 'createdby', 'responsibleemployeename', ...]`
   - These are the fields to search in

**Parser Output:**
```json
{
  "intent": "person",
  "entities": {"person_name": "יניב ליבוביץ"},
  "target_fields": ["updatedby", "createdby", "responsibleemployeename", ...],
  "query_type": "find",
  "original_query": "פניות מיניב ליבוביץ"
}
```

### Supported Intents

1. **Person Query:**
   - Patterns: "מא", "של", "על ידי", "מאת", "מ-"
   - Target fields: updatedby, createdby, responsibleemployeename, contactfirstname, contactlastname
   - Example: "פניות מאור גלילי"

2. **Project Query:**
   - Patterns: "פרויקט", "project", "שם פרויקט"
   - Target fields: projectname, projectdesc
   - Example: "פרויקט אלינור"

3. **Type Query:**
   - Patterns: "מסוג", "סוג", "type"
   - Target fields: requesttypeid
   - Example: "בקשות מסוג 4"

4. **Status Query:**
   - Patterns: "סטטוס", "status", "מצב"
   - Target fields: requeststatusid
   - Example: "בקשות בסטטוס 10"

5. **General Query:**
   - No specific pattern
   - Searches all fields
   - Example: "בקשות על בדיקה"

**Key File:** `scripts/utils/query_parser.py` - Query parsing logic  
**Config File:** `config/search_config.json` - Patterns and mappings

---

## Semantic Search

### How It Works

**Step 1: Generate Query Embedding**
```
"פניות מיניב ליבוביץ"
  ↓
Embedding Model (sentence-transformers/all-MiniLM-L6-v2)
  ↓
Vector: [0.23, -0.45, 0.67, 0.12, ..., 0.89] (384 numbers)
```

**Step 2: Insert into Temp Table**
```sql
CREATE TEMP TABLE temp_query_embedding (embedding vector(384));
INSERT INTO temp_query_embedding VALUES ([0.23, -0.45, ...]);
```

**Step 3: Vector Similarity Search**
```sql
SELECT 
    e.requestid,
    e.chunk_index,
    1 - (e.embedding <=> t.embedding) as similarity
FROM request_embeddings e
CROSS JOIN temp_query_embedding t
WHERE e.embedding IS NOT NULL
ORDER BY similarity DESC
LIMIT 60;  -- Get 3x top_k for deduplication
```

**Why 3x top_k?** To account for multiple chunks per request, then deduplicate.

**Similarity Calculation:**
- `<=>` is cosine distance operator (pgvector)
- `1 - distance` = similarity (0.0 to 1.0)
- Higher similarity = more relevant

---

## Field-Specific Boosting

### Purpose

**Rank exact matches higher** than semantic matches.

### Boosting Logic

**Three boost levels:**

1. **Exact Match in Target Field (2.0x):**
   - If "יניב ליבוביץ" appears in `UpdatedBy` field → boost = 2.0x
   - Highest priority - exact matches rank first

2. **Entity in Chunk (1.5x):**
   - If "יניב ליבוביץ" appears anywhere in chunk text → boost = 1.5x
   - Medium priority - keyword matches rank second

3. **Semantic Similarity (1.0x):**
   - Pure semantic match (no exact text) → boost = 1.0x
   - Lowest priority - semantic matches rank third

### How It Works

**SQL Boosting:**
```sql
SELECT 
    e.requestid,
    similarity,
    CASE
        WHEN r.updatedby ILIKE '%יניב ליבוביץ%' THEN 2.0
        WHEN e.text_chunk ILIKE '%יניב ליבוביץ%' THEN 1.5
        ELSE 1.0
    END as boost
FROM request_embeddings e
JOIN requests r ON e.requestid = r.requestid
CROSS JOIN temp_query_embedding t
ORDER BY (similarity * boost) DESC
```

**Result:** Exact matches rank first, semantic matches rank second.

**Key File:** `api/services.py` - Boosting logic in `SearchService.search()`

---

## Similarity Thresholds

### Purpose

**Filter low-relevance results** from total count calculations.

### Current Thresholds

**For Semantic Queries:**
- **Person/Project queries:** 0.5 (50% similarity)
- **General queries:** 0.4 (40% similarity)

**For Filtered Queries (Type/Status):**
- **No threshold** - Count based on filter only
- More accurate for exact matches

### Why Thresholds?

**Problem:** Without threshold, COUNT query includes very low similarity results (noise).

**Solution:** Apply threshold to COUNT query to filter noise.

**Example:**
```sql
-- Without threshold: Counts all chunks (even 0.1 similarity)
SELECT COUNT(DISTINCT e.requestid) FROM request_embeddings e
WHERE similarity > 0.0  -- Too lenient!

-- With threshold: Only counts relevant chunks
SELECT COUNT(DISTINCT e.requestid) FROM request_embeddings e
WHERE similarity >= 0.5  -- Filters noise
```

**Result:** More accurate total counts (e.g., ~100-400 for person queries instead of 984).

**Key File:** `api/services.py:191-193` - Threshold logic

---

## Total Count Calculation

### How It Works

**For Filtered Queries (Type/Status):**
```sql
-- Count based on filter only (no similarity threshold)
SELECT COUNT(DISTINCT e.requestid)
FROM request_embeddings e
JOIN requests r ON e.requestid = r.requestid
WHERE r.requesttypeid = '4'
```

**Result:** ✅ Perfect accuracy (e.g., "בקשות מסוג 4" = 3,731)

**For Semantic Queries (Person/Project/General):**
```sql
-- Count with similarity threshold
SELECT COUNT(DISTINCT e.requestid)
FROM request_embeddings e
CROSS JOIN temp_query_embedding t
WHERE e.embedding IS NOT NULL
  AND (1 - (e.embedding <=> t.embedding)) >= 0.5  -- Threshold
```

**Result:** ⚠️ Estimated counts (may differ from exact SQL LIKE counts)

**Why Different?**
- Semantic search finds similar meanings, not just exact text
- More flexible than SQL LIKE
- Counts may be higher or lower than exact matches

**This is expected behavior** for semantic search systems.

---

## Complete Search Flow

### Step-by-Step: "פניות מיניב ליבוביץ" → Results

**Step 1: User Input**
```
User types: "פניות מיניב ליבוביץ"
```

**Step 2: Query Parser**
- Pattern "מ" → person query
- Extract "יניב ליבוביץ"
- Target: updatedby, createdby, etc.

**Step 3: Embedding Generation**
- Query → Vector [0.23, -0.45, ...]

**Step 4: Database Search**
- Find vectors similar to [0.23, -0.45, ...]
- Apply boosting (exact matches get 2.0x)
- Rank by (similarity × boost)

**Step 5: Deduplication**
- Group by request ID
- Keep best similarity per request
- Return top 20

**Step 6: Count Total**
- Apply similarity threshold (0.5 for person queries)
- Count all matching requests
- Result: ~100-400 (not 20)

**Step 7: Return Results**
```json
{
  "query": "פניות מיניב ליבוביץ",
  "intent": "person",
  "entities": {"person_name": "יניב ליבוביץ"},
  "results": [...],  // Top 20
  "total_found": 225,  // Total count with threshold
  "search_time_ms": 3421.5
}
```

---

## Configuration

### Top-K Results

**Location:** `api/services.py:75`

**Current:** 20

**How to change:**
```python
def search(self, query: str, top_k: int = 20):
    # Change default from 20 to your desired value
```

**Impact:**
- **More results:** Better coverage, slower
- **Fewer results:** Faster, may miss relevant items

### Similarity Thresholds

**Location:** `api/services.py:191-193`

**Current:**
- Person/Project: 0.5
- General: 0.4

**How to change:**
```python
if intent in ['person', 'project']:
    similarity_threshold = 0.5  # Change to 0.6 for stricter
else:
    similarity_threshold = 0.4  # Change to 0.5 for stricter
```

**Impact:**
- **Higher threshold:** Fewer results, more accurate
- **Lower threshold:** More results, may include noise

### Boost Values

**Location:** `api/services.py:150, 153`

**Current:**
- Exact match: 2.0x
- Entity in chunk: 1.5x
- Semantic: 1.0x

**How to change:**
```python
# Exact match boost
boost = 2.0  # Change to 2.5 for more emphasis

# Entity in chunk boost
boost = 1.5  # Change to 2.0 for more emphasis
```

**Impact:**
- **Higher boost:** More emphasis on exact matches
- **Lower boost:** More emphasis on semantic matches

### Search Limit Multiplier

**Location:** `api/services.py:221`

**Current:** 3x (fetch 60 chunks for top 20 results)

**How to change:**
```python
search_limit = top_k * 3  # Change multiplier
```

**Impact:**
- **Higher multiplier:** More chunks fetched, slower, better deduplication
- **Lower multiplier:** Fewer chunks fetched, faster, may miss results

---

## Making Search More/Less Strict

### More Strict (Fewer Results):

1. **Increase similarity threshold:** `0.5 → 0.6` (person/project), `0.4 → 0.5` (general)
2. **Increase boost values:** `2.0 → 2.5` (exact match), `1.5 → 2.0` (entity in chunk)
3. **Decrease top_k:** `20 → 10` (fewer results returned)

### Less Strict (More Results):

1. **Decrease similarity threshold:** `0.5 → 0.4` (person/project), `0.4 → 0.3` (general)
2. **Decrease boost values:** `2.0 → 1.5` (exact match), `1.5 → 1.2` (entity in chunk)
3. **Increase top_k:** `20 → 30` (more results returned)

---

## Summary

**Complete Search Process:**
1. Parse query (intent, entities, target fields)
2. Generate query embedding (384 numbers)
3. Search database (vector similarity)
4. Apply boosting (exact matches rank higher)
5. Deduplicate (group by request ID)
6. Count total (with similarity threshold)
7. Return results (top-k + total count)

**Key Points:**
- Query parser understands Hebrew patterns
- Semantic search finds by meaning
- Field-specific boosting ranks exact matches first
- Similarity thresholds filter noise
- Total count shows meaningful numbers

**Key Files:**
- `scripts/utils/query_parser.py` - Query parsing
- `api/services.py` - Search logic and boosting
- `config/search_config.json` - Patterns and mappings

---

**Last Updated:** Current Session  
**Status:** Complete and tested

