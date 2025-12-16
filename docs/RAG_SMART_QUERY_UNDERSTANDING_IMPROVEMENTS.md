# RAG Smart Query Understanding - Improvement Plan

## 🎯 Current Limitations

### What We Have Now

**Query Types Detected:**
- `find` - Get requests (default)
- `count` - Count requests ("כמה...?")
- `summarize` - Summarize ("תביא לי סיכום...")
- `similar` - Find similar requests

**Intent Detection:**
- `person` - Person queries ("מאור גלילי")
- `project` - Project queries ("פרויקט אלינור")
- `type` - Type queries ("מסוג 4")
- `status` - Status queries ("סטטוס 1")
- `general` - General semantic search

**Problems:**
1. ❌ Too simple - only detects basic patterns
2. ❌ Doesn't understand complex queries (dates, urgency, comparisons)
3. ❌ Doesn't detect what format user wants (list vs summary vs count)
4. ❌ Fixed prompts don't adapt to query complexity
5. ❌ No support for date-based queries
6. ❌ No support for urgency/priority queries
7. ❌ No support for project counting
8. ❌ No support for answer retrieval from similar requests

---

## 🚀 Proposed Improvements

### 1. Enhanced Query Type Detection

**New Query Types to Support:**

#### A. Count Queries (Enhanced)
```
"כמה פניות יש מאור גלילי?"
"כמה פרויקטים יש לאור גלילי?"
"כמה פניות מסוג 4?"
```
**Detection:**
- "כמה" + entity → count query
- "כמה" + "פרויקטים" → count projects (not requests)
- "כמה" + "פניות" → count requests

**Response Format:**
- Simple count: "נמצאו 225 פניות"
- With breakdown: "נמצאו 225 פניות: 150 פעילות, 75 סגורות"

---

#### B. List Queries (Enhanced)
```
"תביא לי את כל הפניות מאור גלילי"
"הצג את כל הפניות מסוג 4"
"תן לי רשימה של פניות דחופות"
```
**Detection:**
- "תביא לי את כל" → list all
- "הצג" / "תן לי רשימה" → list query
- "כל" + entity → list query

**Response Format:**
- "נמצאו 225 פניות. להלן 20 הראשונות:"
- Then show list (already done)

---

#### C. Summary Queries (Enhanced)
```
"תביא לי סיכום של כל הפניות מאור גלילי"
"סכם את הפניות מסוג 4"
"תן לי סקירה של הפרויקטים"
```
**Detection:**
- "סיכום" / "סכם" / "סקירה" → summary query
- "תביא לי סיכום" → summary query

**Response Format:**
- "נמצאו 225 פניות של אור גלילי. הפניות כוללות:"
- Statistics: breakdown by status, project, type
- Patterns: "רוב הפניות בסטטוס פעיל"
- Top items: "הפרויקטים העיקריים: X (45), Y (32)"

---

#### D. Urgency/Priority Queries (NEW)
```
"מה הפניות הדחופות ביותר?"
"איזה פניות דורשות תשובה דחופה?"
"תביא לי פניות עם תאריך יעד קרוב"
```
**Detection:**
- "דחוף" / "דחופה" / "דחופות" → urgency query
- "תאריך יעד" / "deadline" → date-based urgency
- "קרוב" + "תאריך" → near deadline

**Response Format:**
- "נמצאו 15 פניות דחופות:"
- List with urgency reason: "תאריך יעד: 3 ימים"
- Sorted by urgency

**Implementation:**
- Need to detect date fields in query
- Calculate days until deadline
- Filter by urgency threshold

---

#### E. Date-Based Queries (NEW)
```
"פניות מאור גלילי מהשבוע האחרון"
"כל הפניות שעודכנו ב-10 הימים האחרונים"
"פניות מ-1/1/2024 עד היום"
```
**Detection:**
- "מ-" / "מהשבוע" / "מיום" → date range start
- "עד" / "עד היום" → date range end
- "אחרון" / "אחרונים" → recent (last N days)
- Date patterns: "1/1/2024", "יום ראשון"

**Response Format:**
- "נמצאו 45 פניות מהשבוע האחרון:"
- Include date context in answer

**Implementation:**
- Extract date entities from query
- Parse relative dates ("אחרון" = last 7 days)
- Add date filters to SQL query

---

#### F. Project Counting Queries (NEW)
```
"כמה פרויקטים יש לאור גלילי?"
"מה הפרויקטים של יניב ליבוביץ?"
"איזה פרויקטים יש הכי הרבה פניות?"
```
**Detection:**
- "כמה פרויקטים" → count projects (not requests)
- "מה הפרויקטים" → list projects
- "איזה פרויקטים" → analyze projects

**Response Format:**
- "לאור גלילי יש 12 פרויקטים שונים:"
- List: "1. בנית בנין C1 (45 פניות)"
- Top projects with counts

**Implementation:**
- Group requests by project
- Count per project
- Sort by count

---

#### G. Similar Request Queries (Enhanced)
```
"תביא לי פניות דומות ל-211000001"
"מה הפניות הכי דומות לזו?"
```
**Detection:**
- "דומות" / "דומה" + request ID → similar query
- Request ID pattern: 9 digits

**Response Format:**
- "נמצאו 5 פניות דומות ל-211000001:"
- Explain similarity: "דומות כי: פרויקט זהה, סטטוס דומה"

---

#### H. Answer Retrieval Queries (NEW)
```
"תן לי מענה דומה למענה שניתן לשאילתה 211000001"
"מה המענה שניתן לשאילתה דומה?"
"תביא לי מענה על בסיס פנייה דומה"
```
**Detection:**
- "מענה" + "דומה" → answer retrieval
- "מענה" + request ID → get answer for similar request

**Response Format:**
- "תבסס על פנייה דומה (211000001), המענה הוא:"
- Show answer from similar request
- Explain why it's similar

**Implementation:**
- Find similar request
- Extract answer/response field from that request
- Return as answer

---

### 2. Smart Response Format Selection

**Current:** Fixed format based on query_type

**Proposed:** Dynamic format based on:
1. Query type (count, list, summary, etc.)
2. Query complexity (simple vs complex)
3. Number of results (few vs many)
4. User intent (what they actually want)

**Examples:**

**Simple count:**
```
Query: "כמה פניות יש מאור גלילי?"
Response: "נמצאו 225 פניות של אור גלילי."
```

**Complex count:**
```
Query: "כמה פרויקטים יש לאור גלילי ומה הם?"
Response: "לאור גלילי יש 12 פרויקטים שונים:
1. בנית בנין C1 (45 פניות)
2. פרויקט בדיקה (32 פניות)
..."
```

**Urgent with details:**
```
Query: "מה הפניות הדחופות?"
Response: "נמצאו 15 פניות דחופות:
1. פנייה 211000001 - תאריך יעד: 3 ימים (פרויקט: X)
2. פנייה 211000002 - תאריך יעד: 5 ימים (פרויקט: Y)
..."
```

---

### 3. Enhanced Query Parser

**Current Parser Limitations:**
- Only detects basic patterns
- Doesn't extract dates
- Doesn't detect urgency
- Doesn't understand "projects" vs "requests"

**Proposed Enhancements:**

#### A. Date Entity Extraction
```python
def _extract_date_entities(self, query: str) -> Dict:
    """
    Extract date-related entities:
    - "אחרון" → last 7 days
    - "10 ימים" → last 10 days
    - "1/1/2024" → specific date
    - "מ-X עד Y" → date range
    """
    # Patterns:
    # - "מ-X ימים אחרונים" → last X days
    # - "מ-1/1/2024" → from date
    # - "עד היום" → until today
    # - "מהשבוע האחרון" → last week
```

#### B. Urgency Detection
```python
def _detect_urgency(self, query: str) -> bool:
    """
    Detect if query is about urgency:
    - "דחוף" / "דחופה" / "דחופות"
    - "תאריך יעד" / "deadline"
    - "קרוב" + "תאריך"
    """
```

#### C. Project vs Request Detection
```python
def _detect_entity_type(self, query: str) -> str:
    """
    Detect what entity user is asking about:
    - "פרויקטים" → projects
    - "פניות" / "בקשות" → requests
    - "אנשים" → people
    """
```

#### D. Answer Retrieval Detection
```python
def _detect_answer_retrieval(self, query: str) -> bool:
    """
    Detect if user wants answer from similar request:
    - "מענה" + "דומה"
    - "תשובה" + "דומה"
    - "מענה" + request ID
    """
```

---

### 4. Dynamic Prompt Building

**Current:** Fixed prompts per query_type

**Proposed:** Dynamic prompts based on:
1. Detected query type
2. Extracted entities (dates, urgency, etc.)
3. Query complexity
4. Expected response format

**Example Prompts:**

**Simple Count:**
```
"ספור את הפניות וספק את המספר המדויק בלבד.
ענה: 'נמצאו X פניות.'"
```

**Complex Count (Projects):**
```
"ספור את הפרויקטים השונים וציין כמה פניות יש לכל פרויקט.
ענה בצורה:
'יש X פרויקטים:
1. שם פרויקט (Y פניות)
2. שם פרויקט (Z פניות)
...'"
```

**Urgency Query:**
```
"מצא פניות דחופות (תאריך יעד קרוב) וציין את רמת הדחיפות.
ענה בצורה:
'נמצאו X פניות דחופות:
1. פנייה Y - תאריך יעד: Z ימים (פרויקט: ...)
...'"
```

**Date-Based Query:**
```
"מצא פניות מהתאריכים שצוינו וספק סיכום.
ענה בצורה:
'נמצאו X פניות מהתקופה Y:
[סיכום]'"
```

---

### 5. Implementation Plan

#### Phase 1: Enhanced Query Parser (High Priority)
1. ✅ Add date entity extraction
2. ✅ Add urgency detection
3. ✅ Add project vs request detection
4. ✅ Add answer retrieval detection
5. ✅ Improve query type detection

**Files to modify:**
- `scripts/utils/query_parser.py`
- `config/search_config.json`

---

#### Phase 2: Dynamic Prompt Building (High Priority)
1. ✅ Create prompt templates for each query type
2. ✅ Add dynamic prompt building based on detected entities
3. ✅ Improve response format instructions

**Files to modify:**
- `scripts/core/rag_query.py` (build_prompt method)

---

#### Phase 3: Enhanced Response Formatting (Medium Priority)
1. ✅ Add response formatters for each query type
2. ✅ Implement project counting logic
3. ✅ Implement urgency filtering
4. ✅ Implement date filtering

**Files to modify:**
- `scripts/core/rag_query.py` (format_context, query methods)
- `api/services.py` (SearchService for filtering)

---

#### Phase 4: Answer Retrieval (Low Priority)
1. ✅ Add answer field to database schema (if exists)
2. ✅ Implement similar request finding
3. ✅ Extract answer from similar request
4. ✅ Return as RAG answer

**Files to modify:**
- `scripts/core/rag_query.py` (new method: retrieve_answer_from_similar)
- Database schema (if answer field exists)

---

## 📋 Specific Query Examples & Expected Responses

### Example 1: Simple Count
```
Query: "כמה פניות יש מאור גלילי?"
Detected: count, person
Response: "נמצאו 225 פניות של אור גלילי."
```

### Example 2: Project Count
```
Query: "כמה פרויקטים יש לאור גלילי?"
Detected: count, person, projects
Response: "לאור גלילי יש 12 פרויקטים שונים:
1. בנית בנין C1 (45 פניות)
2. פרויקט בדיקה (32 פניות)
..."
```

### Example 3: Urgent Requests
```
Query: "מה הפניות הדחופות ביותר?"
Detected: urgency, find
Response: "נמצאו 15 פניות דחופות:
1. פנייה 211000001 - תאריך יעד: 3 ימים (פרויקט: X)
2. פנייה 211000002 - תאריך יעד: 5 ימים (פרויקט: Y)
..."
```

### Example 4: Date-Based
```
Query: "פניות מאור גלילי מהשבוע האחרון"
Detected: find, person, date (last 7 days)
Response: "נמצאו 45 פניות של אור גלילי מהשבוע האחרון:
[רשימה]"
```

### Example 5: Answer Retrieval
```
Query: "תן לי מענה דומה למענה שניתן לשאילתה 211000001"
Detected: answer_retrieval, similar (request_id: 211000001)
Response: "תבסס על פנייה דומה (211000001), המענה הוא:
[מענה מהפנייה הדומה]
פנייה זו דומה כי: [הסבר]"
```

---

## 🎯 Priority Order

### High Priority (Do First)
1. ✅ Enhanced query parser (date, urgency, project detection)
2. ✅ Dynamic prompt building
3. ✅ Better query type detection

### Medium Priority
4. ✅ Project counting logic
5. ✅ Urgency filtering
6. ✅ Date filtering

### Low Priority
7. ✅ Answer retrieval from similar requests
8. ✅ Advanced response formatting

---

## 💡 Key Improvements Summary

1. **Smarter Query Understanding:**
   - Detect dates, urgency, projects, answer retrieval
   - Understand complex queries
   - Better entity extraction

2. **Dynamic Response Format:**
   - Adapt to query type
   - Simple vs complex responses
   - Appropriate detail level

3. **Better Prompts:**
   - Query-specific instructions
   - Clear format examples
   - Entity-aware prompts

4. **More Query Types:**
   - Urgency queries
   - Date-based queries
   - Project counting
   - Answer retrieval

---

## 🚀 Next Steps

1. **Enhance query parser** - Add date, urgency, project detection
2. **Improve prompt building** - Dynamic, query-aware prompts
3. **Add filtering logic** - Date, urgency, project grouping
4. **Test with various queries** - Verify smart understanding

This will make the system much smarter and more useful for real-world queries!

