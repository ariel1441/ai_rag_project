# Good RAG Test Questions

## 🎯 What Makes a Good RAG Question?

**RAG is best for questions that need:**
- ✅ **Counting** ("כמה פניות יש...?")
- ✅ **Summarization** ("תביא לי סיכום...")
- ✅ **Analysis** ("מה הפרויקטים העיקריים...?")
- ✅ **Complex reasoning** (multiple criteria, calculations)

**RAG is NOT needed for:**
- ❌ Simple "find" queries (search-only is faster)
- ❌ Just browsing requests
- ❌ Questions that return a list

---

## 📋 Recommended Test Questions

### 1. Count Questions (Best for RAG)

**Question:** `כמה פניות יש מאור גלילי?`

**What RAG should do:**
- Find all requests related to "אור גלילי"
- Count them
- Generate answer: "נמצאו 225 פניות של אור גלילי"

**Why this is good:**
- Needs counting (not just listing)
- RAG adds value (count vs. just showing 20 results)

---

### 2. Summarization Questions

**Question:** `תביא לי סיכום של כל הפניות מסוג 4`

**What RAG should do:**
- Find all type 4 requests
- Analyze them (count, status breakdown, projects)
- Generate summary: "נמצאו 3,731 פניות מסוג 4. רוב הפניות בסטטוס פעיל. הפרויקטים העיקריים הם..."

**Why this is good:**
- Needs analysis, not just listing
- RAG provides summary vs. just showing results

---

### 3. Analysis Questions

**Question:** `מה הפרויקטים העיקריים של אור גלילי?`

**What RAG should do:**
- Find all requests for "אור גלילי"
- Group by project
- Count per project
- Generate: "אור גלילי עובד על מספר פרויקטים: בנית בנין C1 (45 פניות), פרויקט בדיקה (32 פניות)..."

**Why this is good:**
- Needs grouping and analysis
- RAG provides insights vs. just listing

---

### 4. Complex Questions

**Question:** `איזה פניות דורשות תשובה דחופה?`

**What RAG should do:**
- Find requests with urgent status or close deadline
- Analyze urgency criteria
- Generate: "נמצאו 15 פניות דורשות תשובה דחופה. הפניות כוללות..."

**Why this is good:**
- Needs reasoning about multiple criteria
- RAG can explain why they're urgent

---

### 5. Comparison Questions

**Question:** `מה ההבדל בין הפניות של אור גלילי לאלה של יניב ליבוביץ?`

**What RAG should do:**
- Find requests for both people
- Compare (count, types, projects)
- Generate comparison

**Why this is good:**
- Needs comparison logic
- RAG can provide insights

---

## ❌ Questions That DON'T Need RAG

### Simple Find Queries

**Question:** `פניות מאור גלילי`

**What happens:**
- Search-only works perfectly (fast, accurate)
- RAG just adds overhead (slower, same results)
- Intent: "person" (correct)
- Returns: List of requests

**Recommendation:** Use search-only for these!

---

## 🔍 About the "Intent: general" Issue

**What you saw:**
- Search: Intent = "person" ✅ (correct)
- RAG: Intent = "general" ❌ (incorrect)

**Why this might happen:**
1. Different query parsing (should be same, but might be config issue)
2. Query format difference ("פניות מאור גלילי" vs. "תביא לי פניות מאור גלילי")
3. Config not loaded properly in RAG

**Is it a problem?**
- ⚠️ **Minor issue:** Search still works (finds correct requests)
- ⚠️ **Impact:** Might use wrong similarity threshold (0.4 vs 0.5)
- ✅ **Fix needed:** Should use same parser as search

**The good news:**
- Search still finds correct requests
- RAG still generates answer
- Just a minor configuration issue

---

## 💡 Testing Strategy

### Step 1: Test Count Questions
```
כמה פניות יש מאור גלילי?
כמה פניות יש מסוג 4?
כמה פניות יש לפרויקט אלינור?
```

**Expected:**
- Intent: "person" / "type" / "project" (correct)
- Answer: "נמצאו X פניות..."
- Not just a list!

### Step 2: Test Summarization
```
תביא לי סיכום של כל הפניות מסוג 4
תביא לי סיכום של הפניות מאור גלילי
```

**Expected:**
- Answer with statistics
- Breakdown by status/project
- Not just a list!

### Step 3: Test Analysis
```
מה הפרויקטים העיקריים של אור גלילי?
איזה סוגי פניות יש הכי הרבה?
```

**Expected:**
- Grouped/analyzed answer
- Insights, not just data

---

## 🎯 Summary

**Best RAG questions:**
1. ✅ Count questions ("כמה...?")
2. ✅ Summarization ("תביא לי סיכום...")
3. ✅ Analysis ("מה הפרויקטים...?")
4. ✅ Complex reasoning (multiple criteria)

**Don't use RAG for:**
- ❌ Simple find queries (use search-only)
- ❌ Just browsing (use search-only)

**About "intent: general":**
- Minor issue, doesn't break functionality
- Should be fixed to match search
- Search still works correctly

