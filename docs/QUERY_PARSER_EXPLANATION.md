# Query Parser - Understanding User Intent

## 🎯 The Problem You Identified

### Current Search Issues:

**Problem 1: No Query Understanding**
```
Query: "פניות מאור גלילי"
Current: Searches for "אור גלילי" semantically (anywhere)
Should: Search for "אור גלילי" in person fields (updatedby, createdby, etc.)
```

**Problem 2: Hardcoded Keywords**
```
Current: email_keywords = ['מייל', 'email', ...]
Problem: These are arbitrary, not based on real user queries
Problem: Only 3 categories (email, building, general)
Problem: Doesn't understand "מא", "של", etc.
```

**Problem 3: No Field-Specific Search**
```
Query: "פניות מאור גלילי"
Current: Searches all text semantically
Should: Search specifically in updatedby/createdby fields
```

---

## ✅ The Solution: Query Parser

### What Query Parser Does:

**1. Understands Query Intent:**
```
"פניות מאור גלילי" → Intent: person query
"בקשות מסוג 4" → Intent: type query
"פרויקט אלינור" → Intent: project query
```

**2. Extracts Entities:**
```
"פניות מאור גלילי" → Person name: "אור גלילי"
"בקשות מסוג 4" → Type ID: 4
"פרויקט אלינור" → Project name: "אלינור"
```

**3. Determines Target Fields:**
```
Person query → Search in: updatedby, createdby, responsibleemployeename
Project query → Search in: projectname, projectdesc
Type query → Filter by: requesttypeid = 4
```

**4. Detects Query Type:**
```
"תביא לי פניות" → find (return list)
"כמה פניות יש" → count (return number)
"סיכום פניות" → summarize (return summary)
```

---

## 🔧 How It Works

### Example 1: Person Query

**Input:** "פניות מאור גלילי"

**Parser Output:**
```python
{
    'intent': 'person',
    'entities': {'person_name': 'אור גלילי'},
    'target_fields': ['updatedby', 'createdby', 'responsibleemployeename', ...],
    'query_type': 'find',
    'filters': {}
}
```

**Search Action:**
1. Search for "אור גלילי" in target_fields (not all fields)
2. Boost results where name appears in person fields
3. Filter to only show requests with name in person fields

---

### Example 2: Type Query

**Input:** "בקשות מסוג 4"

**Parser Output:**
```python
{
    'intent': 'type',
    'entities': {'type_id': 4},
    'target_fields': ['requesttypeid'],
    'query_type': 'find',
    'filters': {'requesttypeid': 4}
}
```

**Search Action:**
1. Filter: WHERE requesttypeid = 4
2. Then semantic search on filtered results
3. Return type 4 requests

---

### Example 3: Complex Query

**Input:** "תביא לי פניות מסוג 4 מאור גלילי"

**Parser Output:**
```python
{
    'intent': 'person',  # Person is more specific
    'entities': {
        'person_name': 'אור גלילי',
        'type_id': 4
    },
    'target_fields': ['updatedby', 'createdby', ...],
    'query_type': 'find',
    'filters': {'requesttypeid': 4}
}
```

**Search Action:**
1. Filter: WHERE requesttypeid = 4
2. Search for "אור גלילי" in person fields
3. Return matching requests

---

## 📋 Configuration Based on Real Queries

### Your Example Queries → Patterns:

**1. "תביא לי פניות מאור גלילי"**
- Pattern: "מא" → person query
- Target: person fields

**2. "Show me requests where ResponsibleEmployeeName is יניב ליבוביץ"**
- Pattern: "ResponsibleEmployeeName is" → person query
- Target: responsibleemployeename field

**3. "Show me requests like request X"**
- Pattern: "like" → similar query
- Action: Find requests with similar embeddings

**4. "Show me all requests where time left < 3 days"**
- Pattern: "time left" → date calculation
- Action: Calculate and filter (needs RAG or SQL)

**5. "Show me type 4 requests"**
- Pattern: "type 4" or "מסוג 4" → type query
- Filter: requesttypeid = 4

---

## 🎯 What's General vs Project-Specific

### GENERAL (Reusable):
- Query parsing logic
- Intent detection
- Entity extraction
- Query type classification

### PROJECT-SPECIFIC (Config):
- Hebrew patterns ("מא", "של", etc.)
- Field name mappings (Hebrew → English)
- Target fields per intent
- Boost rules

---

## ✅ How This Fixes Your Issues

### Issue 1: "פניות מאור גלילי" doesn't search person fields
**Fix:**
- Parser detects "מא" → person query
- Extracts "אור גלילי" → person name
- Sets target_fields = person fields
- Search only in those fields

### Issue 2: Hardcoded keywords not based on real queries
**Fix:**
- Patterns come from config file
- Based on your example queries
- Easy to add new patterns
- No hardcoding in code

### Issue 3: No field-specific search
**Fix:**
- Parser determines target fields
- Search focuses on those fields
- Boosts exact matches in target fields

---

## 🚀 Next Steps

1. **Test Query Parser** (30 min)
   - Test with your example queries
   - Verify it extracts correctly

2. **Update Search to Use Parser** (2-3 hours)
   - Replace keyword detection with parser
   - Add field-specific search
   - Add boosting for target fields

3. **Test Improved Search** (1 hour)
   - Test "פניות מאור גלילי"
   - Test "בקשות מסוג 4"
   - Verify results are correct

4. **Then Build RAG** (4-8 hours)
   - RAG uses improved search
   - Better results = better answers

