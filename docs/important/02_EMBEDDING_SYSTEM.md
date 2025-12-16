# Embedding System - Complete Guide

**Everything about how embeddings are generated, field weighting, chunking, and lookup tables**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Embedding Model](#embedding-model)
3. [Field Weighting](#field-weighting)
4. [Text Chunking](#text-chunking)
5. [Lookup Tables](#lookup-tables)
6. [Embedding Generation Process](#embedding-generation-process)
7. [Configuration](#configuration)

---

## Overview

**Goal:** Convert database records into searchable vector embeddings.

**What We Do:**
- Combine 83 database fields into weighted text
- Chunk long text into 512-character pieces
- Generate 384-dimensional vectors using embedding model
- Store in `request_embeddings` table

**Result:** 36,031 chunks from 8,195 requests, all searchable via semantic similarity

---

## Embedding Model

### Model Details

**Name:** `sentence-transformers/all-MiniLM-L6-v2`

**Specs:**
- **Dimensions:** 384 numbers per embedding
- **Languages:** Multilingual (Hebrew, English, etc.)
- **Size:** ~500MB (downloads automatically)
- **Speed:** Fast (optimized for speed)
- **Quality:** Good (balance of speed and accuracy)

**Location:** `C:\Users\YourName\.cache\huggingface\hub\` (Windows) or `~/.cache/huggingface/hub/` (Linux/Mac)

**Download:** Automatic on first use, cached locally

### How It Works

```
Input: "Project: בנית בנין C1 | Updated By: אור גלילי"
  ↓
[Model processes text]
  ↓
Output: [0.12, -0.45, 0.89, 0.23, ...] (384 numbers)
```

**Properties:**
- Similar text → Similar numbers
- Different text → Different numbers
- Pre-trained on billions of words
- Understands Hebrew and English

**We don't modify the model** - we use it as-is and customize the INPUT (field weighting, text combination).

---

## Field Weighting

### Why Weight Fields?

**Problem:** Not all fields are equally important for search.

**Solution:** Repeat important fields multiple times in the text.

**How it works:**
- Weight 3.0x: Repeat 3 times (most important)
- Weight 2.0x: Repeat 2 times (important)
- Weight 1.0x: Include once (supporting)
- Weight 0.5x: Include once (specific queries)

### Field Categories

#### Weight 3.0x (Repeat 3 times - HIGHEST PRIORITY)

**Core descriptive text - what users search for most:**

1. `ProjectName` (98.9% coverage)
2. `UpdatedBy` (99.9% coverage) ⭐ **CRITICAL**
3. `ProjectDesc` (39.5% coverage)
4. `AreaDesc` (55.3% coverage)
5. `Remarks` (40.2% coverage)
6. `RequestTypeId` (100% coverage) ⭐ **Important**

#### Weight 2.0x (Repeat 2 times - HIGH PRIORITY)

**Important identifiers and names:**

7. `CreatedBy` (88.1% coverage) ⭐ **CRITICAL**
8. `RequestStatusId` (100% coverage)
9. `RequestTypeReasonId` (39.1% coverage)
10. `ContactFirstName` (44.8% coverage)
11. `ContactLastName` (11.3% coverage)
12. `ContactEmail` (39.8% coverage)
13. `ResponsibleEmployeeName` (26.6% coverage) ⭐ **CRITICAL**
14. `Yazam_ContactName` (21.3% coverage)
15. `Yazam_ContactEmail` (21.0% coverage)
16. `Yazam_CompanyName` (18.4% coverage)

#### Weight 1.0x (Include once - MODERATE PRIORITY)

**Supporting information:**

17. `ResponsibleOrgEntityName` (94.1% coverage)
18. `ResponsibleEmployeeRoleName` (26.6% coverage)
19. `RequestStatusDate` (100% coverage)
20. `PenetrateGroundDesc` (1.6% coverage) - When not empty, important
21. `RequestJobShortDescription` (0.5% coverage) - When not empty, important
22. `ExternalRequestStatusDesc` (8.4% coverage)
23. `ContactPhone` (35.3% coverage)
24. ... and more

#### Weight 0.5x (Include once - LOW PRIORITY)

**Booleans and flags - for specific queries:**

29. `IsPenetrateGround` (90.5% coverage)
30. `IsActive` (100% coverage)
31. `IsConvert` (100% coverage)
32. ... and more

**Coordinates - for spatial queries:**

38. `AreaCenterX` (23.0% coverage)
39. `AreaCenterY` (23.0% coverage)
40. ... and more

### Total Fields

**~44 fields included** in embeddings:
- 🔴 Weight 3.0x: 6 fields
- 🟠 Weight 2.0x: 10 fields
- 🟡 Weight 1.0x: 12 fields
- ⚪ Weight 0.5x: 16 fields

**Excluded:**
- All IDs (RequestId, CompanyId, UserId, etc.) - Not semantic
- All dates (CreatedDate, UpdateDate, etc.) - Not semantic
- Empty fields

**Key File:** `scripts/utils/text_processing.py` - `combine_text_fields_weighted()` function

---

## Text Chunking

### Why Chunk?

**Problem:** Combined text can be 1,000-5,000 characters (too long for optimal embedding).

**Solution:** Split into smaller chunks (512 characters) with overlap (50 characters).

### Chunking Parameters

**Current Values:**
- **Chunk Size:** 512 characters (standard practice)
- **Overlap:** 50 characters (~10% overlap)
- **Max Chunks:** 100 per request (safety limit)

**Why 512?**
- Common limit for many models
- Good balance between context and granularity
- Standard practice in industry

**Why Overlap?**
- Prevents losing context at chunk boundaries
- If "Project: אלינור" is split between chunks, overlap ensures it appears in both

### How It Works

```
Text length: 2000 characters

Chunk 1: characters 0-512
Chunk 2: characters 462-974 (overlaps 50 chars with chunk 1)
Chunk 3: characters 924-1436 (overlaps 50 chars with chunk 2)
Chunk 4: characters 1386-1900 (overlaps 50 chars with chunk 3)
```

**Result:** Multiple chunks per request (average: 4.40 chunks per request)

**Key File:** `scripts/utils/text_processing.py` - `chunk_text()` function

---

## Lookup Tables

### Problem

**Current Issue:**
- Many fields store **IDs** (e.g., `requesttypeid = 4`)
- Descriptive values (e.g., "תכנון") are in separate lookup tables
- Embeddings include "Type: 4" which is **not meaningful** for semantic search
- Users search for **"תכנון"**, not **"4"**

### Solution

**For THIS Project (Now):**
1. Create `config/lookup_mappings.json` with manual ID → Name mappings
2. Update `combine_text_fields_weighted()` to use mappings
3. Include both ID and name: "Type: תכנון (ID: 4)"

**For FUTURE Projects (Automatic):**
1. Auto-detect foreign key relationships
2. Auto-discover lookup tables
3. Auto-build ID → Name mappings
4. Auto-apply during embedding generation

**Status:** Solution designed, ready for implementation

**Key File:** `LOOKUP_TABLES_SOLUTION.md` - Complete solution guide

---

## Embedding Generation Process

### Complete Pipeline

```
Database Request (83 fields)
  ↓
Combine Fields with Weighting (~44 fields, repeated 2-3x)
  ↓
Result: ~1,000-5,000 character string
  ↓
Chunk Text (if >512 chars, with 50 char overlap)
  ↓
Result: Multiple chunks (average 4.40 per request)
  ↓
Generate Embeddings (384 numbers per chunk)
  ↓
Store in Database (request_embeddings table)
```

### Step-by-Step

**Step 1: Load Request**
```python
SELECT * FROM requests WHERE requestid = 211000001
```

**Step 2: Combine Fields**
```python
combined_text = combine_text_fields_weighted(request)
# Result: "Project: בנית בנין C1 | Project: בנית בנין C1 | ..."
```

**Step 3: Chunk Text**
```python
chunks = chunk_text(combined_text, max_chunk_size=512, overlap=50)
# Result: [chunk1, chunk2, chunk3, ...]
```

**Step 4: Generate Embeddings**
```python
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
embeddings = model.encode(chunks)
# Result: [[0.12, -0.45, ...], [0.15, -0.42, ...], ...]
```

**Step 5: Store in Database**
```sql
INSERT INTO request_embeddings 
(requestid, chunk_index, text_chunk, embedding, metadata)
VALUES (?, ?, ?, ?::vector, ?)
```

**Key File:** `scripts/core/generate_embeddings.py` - Main embedding generation script

---

## Configuration

### Chunk Size

**Location:** `scripts/utils/text_processing.py:194`

**Current:** 512 characters

**How to change:**
```python
chunks = chunk_text(text, max_chunk_size=512, overlap=50)
# Change 512 to your desired value
```

**Recommended values:**
- **256:** Smaller chunks, more granular
- **512:** ✅ **Current (standard practice)**
- **1024:** Larger chunks, fewer chunks

### Chunk Overlap

**Location:** `scripts/utils/text_processing.py:194`

**Current:** 50 characters (~10% of 512)

**How to change:**
```python
chunks = chunk_text(text, max_chunk_size=512, overlap=50)
# Change 50 to your desired value
```

**Recommended values:**
- **25:** Less overlap, fewer chunks
- **50:** ✅ **Current (~10% overlap)**
- **100:** More overlap, better context

### Field Weights

**Location:** `scripts/utils/text_processing.py` - `combine_text_fields_weighted()` function

**How to change:**
- Modify the weight categories (3.0x, 2.0x, 1.0x, 0.5x)
- Add/remove fields from each category
- Adjust repetition counts

**After changes:** Regenerate embeddings!

---

## Regenerating Embeddings

### When to Regenerate

- After changing field weights
- After adding/removing fields
- After implementing lookup tables
- After changing chunk size/overlap

### How to Regenerate

```bash
python scripts/core/generate_embeddings.py
```

**Process:**
1. Clears old embeddings
2. Loads all requests from database
3. Combines fields with weighting
4. Chunks text
5. Generates embeddings
6. Stores in database

**Time:** ~1-2 hours for 8,195 requests (36,031 chunks)

---

## Summary

**Complete System:**
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
- Lookup tables improve search quality (to be implemented)

**Key Files:**
- `scripts/utils/text_processing.py` - Field weighting and chunking
- `scripts/core/generate_embeddings.py` - Embedding generation
- `config/lookup_mappings.json` - Lookup table mappings (to be created)

---

**Last Updated:** Current Session  
**Status:** Complete, lookup tables solution designed

