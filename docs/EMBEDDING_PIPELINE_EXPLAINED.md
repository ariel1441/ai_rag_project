# Complete Embedding Pipeline Explained

## 📋 Overview: From Database to Embeddings

Here's the complete step-by-step process of how we convert database records into searchable embeddings:

```
Database Request → Combine Fields → Chunk Text → Generate Embedding → Store in Database
```

---

## 🔄 Step-by-Step Process

### Step 1: Load Request from Database

**What happens:**
```python
SELECT * FROM requests WHERE requestid = 211000001
```

**Result:** Dictionary with 83 fields:
```python
{
    'requestid': 211000001,
    'projectname': 'בנית בנין C1',
    'projectdesc': 'בדיקוש 1',
    'updatedby': 'אור גלילי',
    'createdby': 'אתר חיצוני תמר',
    'contactfirstname': 'Elinor',
    # ... 78 more fields
}
```

---

### Step 2: Combine Text Fields (NEW - With Weighting)

**What happens:** `combine_text_fields_weighted(request)`

**Purpose:** Convert 83 database fields → Single text string with weighting

**How it works:**

#### 2.1: Get Values Safely
```python
def get_value(key):
    value = request.get(key) or request.get(key.lower())
    if value is None or value == '' or str(value).upper() == 'NULL':
        return None
    return str(value).strip()
```
- Handles missing fields
- Converts to string
- Skips empty/NULL values

#### 2.2: Add Fields by Weight

**Weight 3.0x (Repeat 3 times):**
```python
# Critical fields - most important for search
'Project: בנית בנין C1'
'Project: בנית בנין C1'  # Repeated 3x
'Project: בנית בנין C1'  # Repeated 3x
'Updated By: אור גלילי'
'Updated By: אור גלילי'  # Repeated 3x
'Updated By: אור גלילי'  # Repeated 3x
```

**Why repeat?** Embedding models learn better when important information appears multiple times. It's like emphasizing keywords.

**Weight 2.0x (Repeat 2 times):**
```python
'Created By: אתר חיצוני תמר'
'Created By: אתר חיצוני תמר'  # Repeated 2x
'Contact First Name: Elinor'
'Contact First Name: Elinor'  # Repeated 2x
```

**Weight 1.0x (Include once):**
```python
'Responsible Organization: מטה'
'Contact Phone: 0546664931'
```

**Weight 0.5x (Include once, low priority):**
```python
'Is Penetrate Ground: true'
'Area Center: 187796.65, 680045.75'
```

#### 2.3: Join All Fields
```python
combined_text = " | ".join(fields)
```

**Result:** Single string like:
```
Project: בנית בנין C1 | Project: בנית בנין C1 | Project: בנית בנין C1 | Updated By: אור גלילי | Updated By: אור גלילי | Updated By: אור גלילי | Description: בדיקוש 1 | Description: בדיקוש 1 | Description: בדיקוש 1 | Area: תיחום שטח | Area: תיחום שטח | Area: תיחום שטח | Type: 1 | Type: 1 | Type: 1 | Created By: אתר חיצוני תמר | Created By: אתר חיצוני תמר | Status: 2 | Status: 2 | Type Reason: 1.0 | Type Reason: 1.0 | Contact First Name: Elinor | Contact First Name: Elinor | Contact Last Name: Zabari | Contact Email: elinorza2@taldor.co.il | Responsible Employee: יניב ליבוביץ | Responsible Employee: יניב ליבוביץ | Responsible Organization: מטה | Responsible Role: מנהל מערכת | Status Date: 2021-03-24 11:45:38.360 | Contact Phone: 0546664931 | Plan Number: NULL | Request Source Number: NULL | Is Penetrate Ground: true | Is Active: true | Is Convert: false | Is Manual: false | Is Mekorot Layer: false | Is Area File Valid: true | Area Center: 187796.65, 680045.75
```

**Length:** ~1,000-5,000 characters (depends on how many fields have data)

---

### Step 3: Chunk Text (If Too Long)

**What happens:** `chunk_text(combined_text, max_chunk_size=512, overlap=50)`

**Purpose:** Split long text into smaller pieces that fit embedding model limits

**Why chunk?**
- Embedding models work best with focused text (not too long)
- Better semantic meaning per chunk
- Faster processing
- Better search results (smaller, focused chunks)

**How it works:**

#### 3.1: Check if Chunking Needed
```python
if len(text) <= 512:
    return [text]  # No chunking needed
```

#### 3.2: Split into Chunks
```python
# Start at position 0
start = 0
chunks = []

while start < len(text):
    # Take 512 characters
    end = start + 512
    
    # Try to break at sentence boundary (not in middle of word)
    # Look for " | " separator (our field separator)
    if end < len(text):
        last_sep = text.rfind(" | ", start, end)
        if last_sep != -1:
            end = last_sep + 3  # Break after separator
    
    # Extract chunk
    chunk = text[start:end]
    chunks.append(chunk)
    
    # Move forward (with 50 char overlap)
    start = end - 50  # Overlap prevents losing context
```

**Example:**
```
Text length: 2000 characters

Chunk 1: characters 0-512
Chunk 2: characters 462-974 (overlaps 50 chars with chunk 1)
Chunk 3: characters 924-1436 (overlaps 50 chars with chunk 2)
Chunk 4: characters 1386-1900 (overlaps 50 chars with chunk 3)
```

**Why overlap?** Prevents losing context at chunk boundaries. If "Project: אלינור" is split between chunks, overlap ensures it appears in both.

**Result:** List of chunks:
```python
[
    "Project: בנית בנין C1 | Project: בנית בנין C1 | ... (first 512 chars)",
    "... (overlap) | Updated By: אור גלילי | ... (next 512 chars)",
    # ... more chunks if needed
]
```

**Safety limits:**
- Max 100 chunks per request (prevents memory issues)
- Max iterations (prevents infinite loops)

---

### Step 4: Generate Embeddings

**What happens:** `model.encode(chunks)`

**Purpose:** Convert text chunks → Numerical vectors (embeddings)

**How it works:**

#### 4.1: Load Model
```python
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
```
- Downloads once (~500MB)
- Cached locally
- Pre-trained on billions of words

#### 4.2: Process Each Chunk
```python
chunk = "Project: בנית בנין C1 | Updated By: אור גלילי | ..."
embedding = model.encode(chunk)
```

**What the model does:**
1. Tokenizes text (splits into words/subwords)
2. Converts tokens to numbers
3. Processes through neural network
4. Outputs 384 numbers (vector)

**Result:**
```python
embedding = [0.12, -0.45, 0.89, 0.23, ...]  # 384 numbers
```

**Properties:**
- Similar text → Similar numbers
- Different text → Different numbers
- 384 dimensions (model-specific)

#### 4.3: Normalize Embeddings
```python
normalize_embeddings=True
```
- Makes all vectors same length
- Improves similarity calculations
- Standard practice

**Result:** List of embeddings (one per chunk):
```python
[
    [0.12, -0.45, 0.89, ...],  # Embedding for chunk 1
    [0.15, -0.42, 0.91, ...],  # Embedding for chunk 2
    # ... more embeddings
]
```

---

### Step 5: Store in Database

**What happens:** Insert into `request_embeddings` table

**How it works:**

#### 5.1: Prepare Records
```python
for i, chunk in enumerate(chunks):
    embedding = embeddings[i]
    record = (
        request_id,           # "211000001"
        chunk_index,          # 0, 1, 2, ...
        text_chunk,           # Original chunk text
        embedding_str,        # "[0.12, -0.45, 0.89, ...]"
        metadata              # JSON with extra info
    )
```

#### 5.2: Insert in Batches
```python
INSERT INTO request_embeddings 
(requestid, chunk_index, text_chunk, embedding, metadata)
VALUES (?, ?, ?, ?::vector, ?)
```

**Result:** Database table:
```
requestid | chunk_index | text_chunk                    | embedding (vector) | metadata
----------|-------------|-------------------------------|-------------------|----------
211000001 | 0           | "Project: בנית בנין C1 | ..." | [0.12, -0.45, ...] | {...}
211000001 | 1           | "... | Updated By: אור..."    | [0.15, -0.42, ...] | {...}
211000002 | 0           | "Project: ינה חיצוני..."     | [0.18, -0.38, ...] | {...}
```

---

## 🎯 Why This Design?

### Why Weight Fields?
- **Important fields appear more** → Model learns they're important
- **Better search results** → Queries match weighted fields better
- **Semantic understanding** → Model understands "Updated By: אריאל" is important

### Why Chunk?
- **Model limits** → Some models have token limits (though ours doesn't strictly)
- **Better focus** → Smaller chunks = better semantic meaning
- **Faster search** → Smaller vectors = faster comparison

### Why Overlap?
- **No lost context** → Field split between chunks still appears in both
- **Better continuity** → Chunks connect semantically

### Why Store Chunks Separately?
- **Flexible search** → Can search specific parts of request
- **Better results** → Can return exact chunk that matched
- **Metadata** → Can store extra info per chunk

---

## 📊 Example: Complete Flow

**Input:** Request 211000001 from database

**Step 1:** Load request (83 fields)

**Step 2:** Combine fields → ~1,500 character string
```
"Project: בנית בנין C1 | Project: בנית בנין C1 | Project: בנית בנין C1 | Updated By: אור גלילי | Updated By: אור גלילי | Updated By: אור גלילי | ..."
```

**Step 3:** Chunk text → 3 chunks (if >512 chars)
```
Chunk 0: "Project: בנית בנין C1 | ..." (512 chars)
Chunk 1: "... | Updated By: אור גלילי | ..." (512 chars, overlaps 50)
Chunk 2: "... | Contact: Elinor | ..." (remaining chars)
```

**Step 4:** Generate embeddings → 3 vectors (384 numbers each)
```
Embedding 0: [0.12, -0.45, 0.89, ...]
Embedding 1: [0.15, -0.42, 0.91, ...]
Embedding 2: [0.18, -0.38, 0.93, ...]
```

**Step 5:** Store in database → 3 rows in `request_embeddings`

---

## ⚙️ Configuration

**Chunk Size:** 512 characters
- **Why 512?** Common limit for many models, good balance
- **Can be larger?** Yes, but 512 is standard
- **Can be smaller?** Yes, but might lose context

**Overlap:** 50 characters
- **Why 50?** ~10% overlap, prevents lost context
- **Can be larger?** Yes, but creates more chunks
- **Can be smaller?** Yes, but might lose context at boundaries

**Max Chunks:** 100 per request
- **Why limit?** Prevents memory issues
- **What if exceeded?** Returns whole text as single chunk

---

## 🔍 What Happens During Search?

When you search "פניות מאריאל בן עקיבא":

1. **Generate query embedding:**
   ```
   Query: "פניות מאריאל בן עקיבא"
   → Embedding: [0.20, -0.35, 0.85, ...]
   ```

2. **Compare with stored embeddings:**
   ```
   Similarity = 1 - (query_embedding <=> stored_embedding)
   ```

3. **Find top matches:**
   ```
   Request 211000001, Chunk 1: 0.95 similarity
   Request 211000005, Chunk 0: 0.92 similarity
   ...
   ```

4. **Return results:**
   - Shows which chunk matched
   - Shows similarity score
   - Shows original text

---

## ✅ Summary

**Complete Pipeline:**
1. Load request (83 fields) from database
2. Combine fields with weighting (~44 fields, repeated 2-3x)
3. Chunk text if >512 chars (with 50 char overlap)
4. Generate embeddings (384 numbers per chunk)
5. Store in database (one row per chunk)

**Key Points:**
- Weighting emphasizes important fields
- Chunking handles long text
- Overlap prevents lost context
- Multiple chunks per request = better search granularity


