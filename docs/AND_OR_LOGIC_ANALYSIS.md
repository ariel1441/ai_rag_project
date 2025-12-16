# AND/OR Logic Analysis & Solution Plan

## The Problem

### Current Behavior (WRONG):
- "בקשות מאור גלילי" → 142 results
- "בקשות מאור גלילי מסוג 10" → 368 results (MORE! Should be LESS)

**Why this happens:**
1. SQL filters (type_id, status_id) use **AND** logic correctly ✅
2. Semantic search (person_name, project_name) uses **OR** logic ❌
3. The semantic search finds requests similar to the ENTIRE query, which matches:
   - Requests with "אור גלילי" but type != 10
   - Requests with type 10 but no "אור גלילי"  
   - Requests with both

**Root Cause:**
- Semantic search doesn't filter by person_name/project_name - it only boosts
- It searches for similarity to the whole query text
- Multiple entities in query = OR logic (finds any match)

---

## Current Code Analysis

### What Works (AND logic):
```python
# Line 164: SQL filters use AND correctly
if sql_filters:
    request_filter_sql = "WHERE " + " AND ".join(sql_filters)
    # This correctly filters: type_id = 10 AND status_id = 1 AND date >= X
```

### What Doesn't Work (OR logic):
```python
# Semantic search doesn't filter by person_name/project_name
# It only boosts results that contain them
boost_cases.append(f"WHEN e.text_chunk LIKE '%{entity_escaped}%' THEN 1.5")
# But doesn't REQUIRE them to be present
```

**Result:** Semantic search finds requests similar to query, regardless of whether all entities are present.

---

## Solution Requirements

### 1. Detect AND vs OR Intent

**Hebrew Challenges:**
- "ו" (and) - but appears in names: "אור" contains "ו" (technically)
- "או" (or) - but appears in names: "אור" contains "או"
- Can't just search for these words directly

**Approach:**
1. **Default to AND** - Most queries are AND (more restrictive, usually what users want)
2. **Detect explicit OR** - Look for "או" as a separate word (with spaces)
3. **Detect explicit AND** - Look for "ו" as a separate word (with spaces)
4. **Context-aware** - "פניות מאור גלילי" = AND (implicit)
5. **Multiple entities** - "X מסוג Y" = AND (both must match)

### 2. Implement AND Logic

**For AND queries:**
- Apply SQL filters (already works)
- **Also filter semantic results** to require all entities present
- Use stricter similarity threshold
- Require person_name/project_name to appear in results

**For OR queries:**
- Current behavior (semantic similarity to whole query)
- Lower similarity threshold
- Find requests matching ANY entity

### 3. Handle Multiple Entity Types

**Entity Categories:**
1. **Structured (SQL filters):** type_id, status_id, date_range → Already use AND ✅
2. **Text-based (Semantic):** person_name, project_name → Need AND logic ❌
3. **Mixed:** Both types → Need to combine correctly

---

## Proposed Solution

### Phase 1: Default AND Logic (Simple, High Impact)

**Change:**
- When multiple entities detected, require ALL to be present
- For person_name + type_id: Filter results to require both
- Use SQL JOIN to filter semantic results

**Implementation:**
```python
# If we have person_name AND type_id:
# 1. Apply SQL filter for type_id (already done)
# 2. Also filter semantic results to require person_name in text_chunk
# 3. Use stricter similarity threshold

if 'person_name' in entities and 'type_id' in entities:
    # Add additional filter to semantic search
    # Require person_name to appear in text_chunk
    person_name = entities['person_name']
    embedding_where += f" AND e.text_chunk LIKE '%{person_name}%'"
```

**Pros:**
- ✅ Simple to implement
- ✅ Fixes most cases (default AND)
- ✅ High impact (most queries are AND)

**Cons:**
- ❌ Doesn't handle explicit OR
- ❌ Doesn't detect user intent for AND vs OR

---

### Phase 2: Detect AND/OR Intent (Medium Complexity)

**Detect explicit operators:**
- "או" as separate word → OR logic
- "ו" as separate word → AND logic
- No operator → Default AND

**Implementation:**
```python
def detect_logical_operator(query: str) -> str:
    """Detect AND/OR intent from query."""
    # Look for "או" as separate word (with spaces)
    if re.search(r'\s+או\s+', query):
        return 'OR'
    
    # Look for "ו" as separate word (with spaces)  
    if re.search(r'\s+ו\s+', query):
        return 'AND'
    
    # Default: AND (most queries are AND)
    return 'AND'
```

**Pros:**
- ✅ Handles explicit AND/OR
- ✅ Still defaults to AND (safe)
- ✅ Works for most cases

**Cons:**
- ⚠️ Might miss some cases
- ⚠️ Hebrew word boundaries can be tricky

---

### Phase 3: Advanced Intent Detection (Complex)

**Use query structure:**
- "X מסוג Y" → AND (both required)
- "X או Y" → OR (either is fine)
- "X ו-Y" → AND (both required)
- Multiple entities without operator → AND (default)

**Implementation:**
```python
def analyze_query_structure(parsed: Dict) -> str:
    """Analyze query structure to determine AND/OR."""
    entities = parsed.get('entities', {})
    
    # If multiple entities, check for explicit operators
    if len(entities) > 1:
        query = parsed.get('original_query', '')
        
        # Check for explicit OR
        if has_explicit_or(query):
            return 'OR'
        
        # Check for explicit AND
        if has_explicit_and(query):
            return 'AND'
        
        # Default: AND (more restrictive, usually what users want)
        return 'AND'
    
    # Single entity: no AND/OR needed
    return 'AND'
```

**Pros:**
- ✅ Most accurate
- ✅ Handles complex cases
- ✅ Still defaults to AND

**Cons:**
- ❌ More complex
- ❌ Might need tuning

---

## Implementation Plan

### Option 1: Quick Fix (Default AND) - **RECOMMENDED**

**Difficulty:** ⭐⭐ (Medium)
**Quality:** ⭐⭐⭐⭐ (Very Good)
**Impact:** ⭐⭐⭐⭐⭐ (High)

**What to do:**
1. When multiple entities detected, require ALL in results
2. Filter semantic results to require person_name/project_name
3. Use SQL JOIN to combine filters

**Time:** 2-3 hours
**Risk:** Low (defaults to more restrictive, which is usually correct)

---

### Option 2: Detect AND/OR Intent

**Difficulty:** ⭐⭐⭐ (Medium-Hard)
**Quality:** ⭐⭐⭐⭐⭐ (Excellent)
**Impact:** ⭐⭐⭐⭐⭐ (High)

**What to do:**
1. Detect explicit "או" and "ו" operators
2. Implement AND logic (filter all entities)
3. Implement OR logic (current behavior)
4. Default to AND when unclear

**Time:** 4-6 hours
**Risk:** Medium (need to handle Hebrew word boundaries carefully)

---

### Option 3: Advanced Intent Detection

**Difficulty:** ⭐⭐⭐⭐ (Hard)
**Quality:** ⭐⭐⭐⭐⭐ (Excellent)
**Impact:** ⭐⭐⭐⭐⭐ (High)

**What to do:**
1. Analyze query structure
2. Detect implicit AND/OR from context
3. Use ML/NLP for intent detection
4. Fallback to default AND

**Time:** 8-12 hours
**Risk:** High (complex, might have edge cases)

---

## Recommendation

**Start with Option 1 (Quick Fix):**
- ✅ Fixes the immediate problem (AND logic)
- ✅ Simple to implement
- ✅ Low risk
- ✅ High impact

**Then add Option 2 (Detect AND/OR):**
- ✅ Handles explicit operators
- ✅ Still defaults to AND (safe)
- ✅ Good user experience

**Skip Option 3 (for now):**
- ⚠️ Too complex for initial fix
- ⚠️ Can add later if needed

---

## Expected Results After Fix

### Before:
- "בקשות מאור גלילי" → 142 results
- "בקשות מאור גלילי מסוג 10" → 368 results ❌ (MORE!)

### After (Option 1):
- "בקשות מאור גלילי" → 142 results
- "בקשות מאור גלילי מסוג 10" → ~50-100 results ✅ (LESS, both required)

### After (Option 2):
- "בקשות מאור גלילי" → 142 results
- "בקשות מאור גלילי מסוג 10" → ~50-100 results ✅ (AND - both required)
- "בקשות מאור גלילי או מסוג 10" → ~400 results ✅ (OR - either is fine)

---

## Importance Assessment

**Criticality:** ⭐⭐⭐⭐⭐ (Very High)

**Why:**
- ✅ Fundamental search behavior
- ✅ Users expect AND logic by default
- ✅ Current behavior is confusing (more results with more filters)
- ✅ Affects all multi-entity queries

**Impact:**
- **High** - Fixes major usability issue
- **Wide** - Affects many query types
- **User-facing** - Directly impacts search results

---

## Next Steps

1. **Implement Option 1** (Default AND logic)
2. **Test with your examples**
3. **Add Option 2** (Detect AND/OR) if needed
4. **Monitor user queries** to see if more cases need handling

**Ready to implement?** Let me know and I'll start with Option 1!

