# How to Improve Accuracy - Complete Guide

**Focus:** Using "Similar Requests" as example, but applies to all query types.

---

## Current Implementation Issues

### For "Similar Requests" (`similar` query type):

**Current Problems:**
1. ❌ **Doesn't use request ID properly** - Just does semantic search on query text
2. ❌ **Generic explanations** - LLM gives vague "they're similar" answers
3. ❌ **No similarity scores shown** - User can't see how similar they are
4. ❌ **No field comparison** - Doesn't highlight what fields match
5. ❌ **Limited context** - Only shows basic fields

---

## Improvement Strategy

### 1. **Use Request ID to Find Actual Request** (Critical Fix)

**Current:** Query "פניות דומות ל-211000001" → embeds query text → finds similar

**Better:** Query "פניות דומות ל-211000001" → finds request 211000001 → uses its embedding → finds similar

**Implementation:**

```python
def retrieve_similar_requests(self, request_id: str, top_k: int = 20) -> List[Dict]:
    """
    Find requests similar to a specific request ID.
    Uses the actual request's embedding, not query text.
    """
    if not self.conn:
        self.connect_db()
    
    # 1. Find the source request's embedding
    self.cursor.execute("""
        SELECT embedding, requestid
        FROM request_embeddings
        WHERE requestid = %s
        ORDER BY chunk_index
        LIMIT 1
    """, (request_id,))
    
    source_result = self.cursor.fetchone()
    if not source_result:
        return []  # Request not found
    
    source_embedding = source_result[0]
    
    # 2. Find similar requests (exclude source)
    self.cursor.execute("""
        SELECT 
            e.requestid,
            e.chunk_index,
            1 - (e.embedding <=> %s::vector) as similarity
        FROM request_embeddings e
        WHERE e.embedding IS NOT NULL
          AND e.requestid != %s
        ORDER BY e.embedding <=> %s::vector
        LIMIT %s
    """, (source_embedding, request_id, source_embedding, top_k * 3))
    
    # ... rest of deduplication logic
```

**Impact:** ✅ **HUGE** - Finds actually similar requests, not just semantically similar to query text

---

### 2. **Show Similarity Scores & Field Matches**

**Current:** Just lists requests, no indication of similarity

**Better:** Show similarity score and highlight matching fields

**Implementation:**

```python
def format_similar_context(self, source_request: Dict, similar_requests: List[Dict], 
                          similarity_scores: Dict[str, float]) -> str:
    """
    Format context showing what makes requests similar.
    """
    context_parts = []
    context_parts.append(f"פנייה מקור: {source_request['requestid']}")
    context_parts.append(f"פרויקט: {source_request.get('projectname', 'N/A')}")
    context_parts.append(f"סוג: {source_request.get('requesttypeid', 'N/A')}")
    context_parts.append(f"סטטוס: {source_request.get('requeststatusid', 'N/A')}")
    context_parts.append("")
    context_parts.append(f"נמצאו {len(similar_requests)} פניות דומות:\n")
    
    for i, req in enumerate(similar_requests, 1):
        req_id = req['requestid']
        similarity = similarity_scores.get(req_id, 0.0)
        
        parts = [f"פנייה {req_id} (דמיון: {similarity:.2%})"]
        
        # Highlight matching fields
        if req.get('projectname') == source_request.get('projectname'):
            parts.append(f"✓ אותו פרויקט: {req['projectname']}")
        
        if req.get('requesttypeid') == source_request.get('requesttypeid'):
            parts.append(f"✓ אותו סוג: {req['requesttypeid']}")
        
        if req.get('requeststatusid') == source_request.get('requeststatusid'):
            parts.append(f"✓ אותו סטטוס: {req['requeststatusid']}")
        
        if req.get('updatedby') == source_request.get('updatedby'):
            parts.append(f"✓ אותו מעדכן: {req['updatedby']}")
        
        context_parts.append(f"{i}. {' | '.join(parts)}")
    
    return "\n".join(context_parts)
```

**Impact:** ✅ **HIGH** - LLM can see what makes them similar, generates better explanations

---

### 3. **Better Prompts with Specific Instructions**

**Current:** Generic "explain why they're similar"

**Better:** Specific instructions about what to highlight

**Implementation:**

```python
def _build_similar_instruction(self, source_request: Dict, entities: Dict) -> str:
    """
    Build specific instruction for similar requests.
    """
    request_id = entities.get('request_id')
    source_project = source_request.get('projectname', 'N/A')
    source_type = source_request.get('requesttypeid', 'N/A')
    source_status = source_request.get('requeststatusid', 'N/A')
    
    instruction = f"""הסבר מדוע הפניות האלה דומות לשאילתה {request_id}.

פנייה מקור {request_id}:
- פרויקט: {source_project}
- סוג: {source_type}
- סטטוס: {source_status}

הסבר:
1. ציין כמה פניות נמצאו ומה רמת הדמיון הממוצעת
2. ציין מה המשותף (פרויקט, סוג, סטטוס, אנשים, וכו')
3. ציין הבדלים עיקריים (אם יש)
4. הסבר מדוע הפניות האלה רלוונטיות

ענה בצורה:
"נמצאו X פניות דומות לשאילתה {request_id} (דמיון ממוצע: Y%).
הפניות דומות כי:
- כולן באותו פרויקט ({source_project})
- כולן מאותו סוג ({source_type})
- כולן בסטטוס {source_status}
[הסבר נוסף על דמיון בתיאור, מיקום, וכו']
הבדלים עיקריים: [אם יש]"
"""
    return instruction
```

**Impact:** ✅ **HIGH** - LLM gets specific guidance, generates better explanations

---

### 4. **Calculate Field-Level Similarity**

**Current:** Only semantic similarity

**Better:** Also calculate field-level matches

**Implementation:**

```python
def calculate_field_similarity(self, source: Dict, target: Dict) -> Dict[str, bool]:
    """
    Calculate which fields match between two requests.
    """
    matches = {}
    
    # Exact matches
    matches['same_project'] = source.get('projectname') == target.get('projectname')
    matches['same_type'] = source.get('requesttypeid') == target.get('requesttypeid')
    matches['same_status'] = source.get('requeststatusid') == target.get('requeststatusid')
    matches['same_updater'] = source.get('updatedby') == target.get('updatedby')
    matches['same_creator'] = source.get('createdby') == target.get('createdby')
    matches['same_responsible'] = source.get('responsibleemployeename') == target.get('responsibleemployeename')
    
    # Similar dates (within 30 days)
    if source.get('requeststatusdate') and target.get('requeststatusdate'):
        try:
            from datetime import datetime, timedelta
            source_date = datetime.strptime(str(source['requeststatusdate'])[:10], '%Y-%m-%d')
            target_date = datetime.strptime(str(target['requeststatusdate'])[:10], '%Y-%m-%d')
            days_diff = abs((source_date - target_date).days)
            matches['similar_date'] = days_diff <= 30
        except:
            matches['similar_date'] = False
    else:
        matches['similar_date'] = False
    
    return matches
```

**Impact:** ✅ **MEDIUM** - More accurate similarity detection

---

### 5. **Retrieve More Context for Similar Requests**

**Current:** Only 20 requests

**Better:** Retrieve more, then filter by similarity threshold

**Implementation:**

```python
# In retrieve_similar_requests:
# Retrieve more candidates
top_k_candidates = top_k * 5  # Get 5x more

# Filter by similarity threshold
SIMILARITY_THRESHOLD = 0.6  # Only requests with >60% similarity
filtered = [
    req for req in candidates 
    if similarity_scores[req['requestid']] >= SIMILARITY_THRESHOLD
]

# Return top_k from filtered
return filtered[:top_k]
```

**Impact:** ✅ **MEDIUM** - Better quality similar requests

---

## Complete Implementation for Similar Requests

### Step 1: Add Method to RAGSystem

```python
def retrieve_similar_requests(self, request_id: str, top_k: int = 20, 
                             similarity_threshold: float = 0.6) -> tuple[List[Dict], Dict[str, float]]:
    """
    Find requests similar to a specific request ID.
    
    Returns:
        (list of similar requests, similarity scores dict)
    """
    # Implementation from above
    ...
```

### Step 2: Update Query Method

```python
# In query() method:
if query_type == 'similar' and 'request_id' in entities:
    request_id = entities['request_id']
    
    # Fetch source request
    source_request = self._fetch_request_by_id(request_id)
    if not source_request:
        return {
            'answer': f'לא נמצאה שאילתה {request_id}.',
            'requests': [],
            'parsed': parsed,
            'context': 'Request not found.'
        }
    
    # Find similar requests using source request's embedding
    similar_requests, similarity_scores = self.retrieve_similar_requests(
        request_id, top_k=top_k, similarity_threshold=0.6
    )
    
    # Format context with field matches
    context = self.format_similar_context(source_request, similar_requests, similarity_scores)
    
    # Build better prompt
    instruction = self._build_similar_instruction(source_request, entities)
    # ... rest of prompt building
```

### Step 3: Update Format Context

```python
def format_similar_context(self, source_request: Dict, similar_requests: List[Dict],
                          similarity_scores: Dict[str, float]) -> str:
    """
    Format context showing similarity details.
    """
    # Implementation from above
    ...
```

---

## Improvements for Other Query Types

### For `find` (General Queries):

1. **Better field weighting** - Adjust weights based on query intent
2. **More context** - Include more fields in context
3. **Better prompts** - More specific about what to summarize

### For `count`:

1. **Verify count** - Compare with database count
2. **Show breakdown** - Count by type, status, project
3. **Handle edge cases** - Zero results, very large counts

### For `summarize`:

1. **Retrieve more requests** - 50-100 instead of 20
2. **Calculate statistics** - Pre-calculate stats, give to LLM
3. **Better formatting** - Structured statistics format

### For `urgent`:

1. **Better date calculations** - More accurate days until deadline
2. **Priority levels** - Categorize by urgency (1-3 days, 4-7 days)
3. **Sort by urgency** - Most urgent first

### For `answer_retrieval`:

1. **Map answer fields** - Identify which fields contain "answers"
2. **Extract directly** - Use field mapping, not LLM extraction
3. **Fallback logic** - If no answer field, use LLM to generate

---

## Testing Strategy

### 1. **Test Similar Requests:**

```python
# Test queries:
"תביא לי פניות דומות ל-211000001"
"מצא פניות דומות לשאילתה 211000001"
"פניות דומות ל-211000001"

# What to check:
- ✅ Does it find the source request?
- ✅ Are similar requests actually similar?
- ✅ Do similarity scores make sense?
- ✅ Does LLM explanation highlight correct fields?
- ✅ Are field matches accurate?
```

### 2. **Measure Improvement:**

**Before:**
- Generic explanations: "הפניות דומות כי..."
- No similarity scores
- Might not find actually similar requests

**After:**
- Specific explanations: "הפניות דומות כי: אותו פרויקט (X), אותו סוג (Y)..."
- Similarity scores shown
- Finds actually similar requests (using source embedding)

---

## Expected Improvement

### Similar Requests:

**Current:** 75-85% accuracy (generic explanations)

**After improvements:**
- ✅ **90-95% accuracy** (specific, accurate explanations)
- ✅ **Better retrieval** (uses source request embedding)
- ✅ **More useful** (shows similarity scores, field matches)

### Other Types:

- **find:** 85-95% → **90-97%** (better context, prompts)
- **count:** 95-100% → **98-100%** (verification, breakdown)
- **summarize:** 70-85% → **80-90%** (more context, pre-calculated stats)
- **urgent:** 90-95% → **93-97%** (better date calculations)
- **answer_retrieval:** 60-75% → **75-85%** (field mapping)

---

## Implementation Priority

### High Priority (Biggest Impact):

1. ✅ **Use request ID for similar requests** (Critical fix)
2. ✅ **Show similarity scores** (High value)
3. ✅ **Better prompts** (Easy, high impact)

### Medium Priority:

4. ✅ **Field-level similarity** (More accurate)
5. ✅ **Retrieve more context** (Better quality)

### Low Priority (Polish):

6. ✅ **Better formatting** (Nice to have)
7. ✅ **Edge case handling** (Robustness)

---

## Code Location

**Files to modify:**
- `scripts/core/rag_query.py` - Add `retrieve_similar_requests()` method
- `scripts/core/rag_query.py` - Update `query()` method for similar queries
- `scripts/core/rag_query.py` - Add `format_similar_context()` method
- `scripts/core/rag_query.py` - Update `_build_dynamic_instruction()` for similar

**Estimated time:** 2-3 hours for similar requests improvements

---

## Summary

**For Similar Requests:**
1. ✅ Use request ID to find source request
2. ✅ Use source request's embedding to find similar
3. ✅ Show similarity scores and field matches
4. ✅ Better prompts with specific instructions
5. ✅ Calculate field-level similarity

**Expected result:** 75-85% → **90-95% accuracy**

**The key insight:** Don't search for "similar to query text" - search for "similar to the actual request"!

