# Search Filtering Changes - What Was Added

## 🔍 What Changed in `search.py`

### Problem:
When searching "פניות מאריאל בן עקיבא", you got:
- ✅ Correct results: Requests with "אריאל בן עקיבא" in `updatedby`
- ❌ Wrong results: Requests with same project name but different person

**Example:** Requests with project "תוספת יחידות דיור" appeared even though they don't have "אריאל בן עקיבא"

---

## ✅ What Was Added

### 1. Person Name Detection
```python
# Check if query looks like a person name
query_words = query.lower().split()
is_person_query = len(query_words) >= 2 or any(word in query_lower for word in ['מאת', 'מא', 'של', 'על ידי'])
```

**What it does:**
- Detects if query is likely a person name (2+ words, or contains "מא", "של", etc.)
- Example: "פניות מאריאל בן עקיבא" → detected as person query

---

### 2. Post-Filtering (After Search)
```python
# Filter: Only keep requests where query appears in person-related fields
if is_person_query:
    for req_id in unique_request_ids:
        # Check if query appears in:
        # - updatedby
        # - createdby
        # - responsibleemployeename
        # - contactfirstname
        # - contactlastname
        
        if has_match:
            filtered_request_ids.append(req_id)
        # If no match but similarity is very high (>0.7), keep it (might be correct)
        elif request_scores[req_id]['best_similarity'] > 0.7:
            filtered_request_ids.append(req_id)
```

**What it does:**
- After semantic search finds results
- Filters to only show requests where person name appears in person fields
- Keeps high-similarity results (>0.7) even if no exact match (might be correct)

---

### 3. Result Limiting
```python
# Get top 50 for filtering, then filter down to top 20
unique_request_ids = [req_id for req_id, _ in sorted_requests[:50]]
# ... filtering ...
if len(filtered_request_ids) >= 3:
    unique_request_ids = filtered_request_ids[:20]
else:
    # If too few results, show top 10 by similarity
    unique_request_ids = [req_id for req_id, _ in sorted_requests[:10]]
```

**What it does:**
- Gets top 50 results for filtering
- Filters to only matching requests
- Shows top 20 filtered results
- If too few results (<3), shows top 10 by similarity (might be correct)

---

## 🎯 How It Works Now

### Before (Old Search):
```
Query: "פניות מאריאל בן עקיבא"
    ↓
[Semantic search] → Finds similar requests
    ↓
Results: 
  - Requests with "אריאל בן עקיבא" ✅
  - Requests with same project ❌ (wrong!)
```

### After (With Filtering):
```
Query: "פניות מאריאל בן עקיבא"
    ↓
[Semantic search] → Finds similar requests
    ↓
[Person name detection] → Detects it's a person query
    ↓
[Post-filtering] → Only keeps requests with person name in person fields
    ↓
Results:
  - Requests with "אריאל בן עקיבא" ✅
  - Requests with same project ❌ (filtered out!)
```

---

## ⚠️ Important Notes

### This is a TEMPORARY Fix

**Why:**
- Works around the problem (old embeddings don't include `updatedby`)
- Filters results after search (less efficient)
- Might filter out correct results if similarity is low

**Real Fix:**
- Regenerate embeddings with `updatedby` included
- Semantic search will find correct requests from the start
- No need for post-filtering

---

## 📊 When Filtering Applies

**Applies when:**
- Query has 2+ words (likely person name)
- Query contains "מא", "של", "על ידי", "מאת"
- Display choice is "2" (full details)

**Doesn't apply when:**
- Display choice is "1" (IDs only)
- Query is single word
- Query doesn't look like person name

---

## ✅ Summary

**What changed:**
1. Added person name detection
2. Added post-filtering to remove irrelevant results
3. Improved result limiting

**Why:**
- Temporary fix for old embeddings issue
- Removes "תוספת יחידות דיור" results that don't have person name

**Next step:**
- Regenerate embeddings (real fix)
- Then this filtering might not be needed (or can be improved)

---

## 🚀 After Regenerating Embeddings

Once you regenerate embeddings with `updatedby` included:
- Semantic search will find correct requests from the start
- Filtering might still be useful (to ensure exact matches)
- Or we can remove it if search is accurate enough

**Test both:**
1. Search with new embeddings (no filtering needed?)
2. If still issues, keep filtering but improve it
3. Or remove filtering if search is perfect

