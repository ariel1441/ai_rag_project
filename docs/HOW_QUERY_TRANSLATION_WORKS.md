# How Query Translation Works - From Human Prompt to Search

## 🔄 Complete Flow: "פניות מיניב ליבוביץ" → Search Results

### Step 1: User Input
```
User types: "פניות מיניב ליבוביץ"
```

---

### Step 2: Query Parser (Understanding Intent)

**What it does:**
- Analyzes the query text
- Looks for patterns (Hebrew words like "מא", "של", "פרויקט")
- Extracts entities (names, IDs, dates)
- Determines intent (what user wants)

**For "פניות מיניב ליבוביץ":**

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
  "entities": {
    "person_name": "יניב ליבוביץ"
  },
  "target_fields": [
    "updatedby",
    "createdby", 
    "responsibleemployeename",
    "contactfirstname",
    "contactlastname"
  ],
  "query_type": "find",
  "original_query": "פניות מיניב ליבוביץ"
}
```

---

### Step 3: Embedding Model (Convert to Numbers)

**What it does:**
- Takes the original query text
- Converts it to a vector (384 numbers)
- This vector represents the "meaning" of the query

**Process:**
```
"פניות מיניב ליבוביץ"
  ↓
Embedding Model (sentence-transformers/all-MiniLM-L6-v2)
  ↓
Vector: [0.23, -0.45, 0.67, 0.12, ..., 0.89] (384 numbers)
```

**Why vectors?**
- Similar queries → Similar vectors
- Easy to compare with database vectors
- Finds semantically similar requests

---

### Step 4: Database Search (Vector Similarity)

**What it does:**
- Compares query vector with all stored embeddings
- Finds most similar vectors (cosine similarity)
- Uses field-specific boosting

**Process:**

1. **Insert query vector into temp table:**
   ```sql
   CREATE TEMP TABLE temp_query_embedding (embedding vector(384));
   INSERT INTO temp_query_embedding VALUES ([0.23, -0.45, ...]);
   ```

2. **Search with boosting:**
   ```sql
   SELECT requestid, similarity, boost
   FROM request_embeddings e
   CROSS JOIN temp_query_embedding t
   WHERE e.embedding IS NOT NULL
   ORDER BY (similarity * boost) DESC
   LIMIT 60;  -- Get 3x top_k for deduplication
   ```

3. **Field-Specific Boosting:**
   - If "יניב ליבוביץ" appears in `UpdatedBy` field → boost = 2.0x
   - If appears in chunk text → boost = 1.5x
   - Semantic similarity → boost = 1.0x
   - **Result:** Exact matches rank higher!

---

### Step 5: Deduplication & Ranking

**What it does:**
- Groups results by request ID
- Keeps best similarity per request
- Ranks by (similarity × boost)
- Returns top 20

**Process:**
```
Chunk results: [
  (211000001, chunk_0, similarity=0.95, boost=2.0),
  (211000001, chunk_1, similarity=0.90, boost=1.5),
  (211000002, chunk_0, similarity=0.88, boost=2.0),
  ...
]

After grouping by request ID:
{
  211000001: {best_similarity: 0.95, boost: 2.0, score: 1.90},
  211000002: {best_similarity: 0.88, boost: 2.0, score: 1.76},
  ...
}

After sorting by score:
[211000001, 211000002, ...]  -- Top 20
```

---

### Step 6: Get Full Request Data

**What it does:**
- Fetches full details for top 20 request IDs
- Includes: projectname, updatedby, createdby, etc.

**SQL:**
```sql
SELECT requestid, projectname, updatedby, createdby, ...
FROM requests
WHERE requestid IN (211000001, 211000002, ...)
```

---

### Step 7: Count Total Matches

**What it does:**
- Counts ALL matching requests (not just top 20)
- Uses same search query but COUNT instead of SELECT

**SQL:**
```sql
SELECT COUNT(DISTINCT e.requestid)
FROM request_embeddings e
CROSS JOIN temp_query_embedding t
WHERE e.embedding IS NOT NULL
  AND (similarity * boost) > threshold
```

**Result:** total_count = 225 requests

---

### Step 8: Return Results

**Response:**
```json
{
  "query": "פניות מיניב ליבוביץ",
  "intent": "person",
  "entities": {"person_name": "יניב ליבוביץ"},
  "results": [
    {
      "requestid": "211000001",
      "similarity": 0.95,
      "boost": 2.0,
      "projectname": "פרויקט יניב בדיקת הדרכות",
      "updatedby": "יניב ליבוביץ",
      ...
    },
    ...
  ],
  "total_found": 225,
  "search_time_ms": 3421.5
}
```

---

## 🎯 Key Components

### 1. Query Parser
**Purpose:** Understand what user wants
- Pattern matching (Hebrew words)
- Entity extraction (names, IDs)
- Intent detection (person/project/type)
- **No AI model** - just pattern matching and rules

### 2. Embedding Model
**Purpose:** Convert text to searchable vectors
- Model: sentence-transformers/all-MiniLM-L6-v2
- Input: Query text
- Output: 384-dimensional vector
- **Always loaded** (small, fast)

### 3. Database Search
**Purpose:** Find similar requests
- Vector similarity search (pgvector)
- Field-specific boosting
- SQL queries with vector operations

### 4. Boosting System
**Purpose:** Rank exact matches higher
- Exact match in target field: 2.0x
- Entity in chunk: 1.5x
- Semantic similarity: 1.0x

---

## 📊 Example: Complete Translation

**Input:** "פניות מיניב ליבוביץ"

**Step-by-step:**

1. **Parser:**
   - Pattern "מ" → person query
   - Extract "יניב ליבוביץ"
   - Target: updatedby, createdby, etc.

2. **Embedding:**
   - Query → Vector [0.23, -0.45, ...]

3. **Search:**
   - Find vectors similar to [0.23, -0.45, ...]
   - Boost if "יניב ליבוביץ" in UpdatedBy (2.0x)
   - Rank by (similarity × boost)

4. **Results:**
   - Top 20 requests
   - Total: 225 requests found

---

## 🔍 Why This Works

**Semantic Search:**
- Finds requests even if exact text doesn't match
- "פניות מיניב" finds "יניב ליבוביץ" requests
- Understands meaning, not just keywords

**Field-Specific:**
- Knows to search UpdatedBy/CreatedBy for person queries
- Not searching all fields randomly
- More accurate results

**Boosting:**
- Exact matches rank first
- Semantic matches rank second
- Best of both worlds

---

## 💡 Summary

**Translation Process:**
```
Human Query
  ↓
Query Parser (pattern matching, entity extraction)
  ↓
Embedding Model (text → vector)
  ↓
Database Search (vector similarity + boosting)
  ↓
Results (top 20 + total count)
```

**No LLM needed for search!** Just:
- Pattern matching (parser)
- Embedding model (lightweight)
- Vector search (database)

**LLM only used for Type 3** (generating text answers).

