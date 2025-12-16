# Demo Questions and Testing Guide

## 📊 Data Overview

**Total Requests:** 8,195

**Key Statistics:**
- **Request Types:** Type 4 (3,731), Type 1 (2,114), Type 3 (1,339), Type 2 (999)
- **Request Status:** Status 10 (4,217), Status 1 (1,268), Status 7 (769)
- **Top People (UpdatedBy):** TamarApp (4,217), אוגלבו משה (1,151), יניב ליבוביץ (120), אוקסנה כלפון (78)
- **Top People (CreatedBy):** TamarApp (4,823), אתר חיצוני תמר (548), אוגלבו משה (380), יניב ליבוביץ (23)
- **Top Projects:** בדיקה (61), תיאום תכנון באזור חדרה (31), בדיקה אור גלילי (27)

---

## 🎯 Demo Questions for Testing

### Question 1: Person Query - יניב ליבוביץ
**Query:** `פניות מיניב ליבוביץ`  
**English:** Requests from יניב ליבוביץ  
**Type:** Person query  

**Expected Results for Type 1 (חיפוש בלבד):**
- **Total Count:** 225 requests (will show "נמצאו 225 בקשות")
- **Displayed:** Top 20 requests (shows "מציג 20 הראשונות")
- **Sample Request IDs:** 211000001, 211000002, 211000003, 211000004, 211000118, 211000160, 211000229, 211000272, 211000292, 211000297
- **Should find in fields:** UpdatedBy, CreatedBy, ResponsibleEmployeeName
- **Response:** List of requests with details, no text answer
- **Speed:** ~3-5 seconds

**Expected Results for Type 3 (RAG - עם תשובה מלאה):**
- **Total Count:** 225 requests
- **Displayed:** Top 20 requests
- **Text Answer:** "נמצאו 225 פניות של יניב ליבוביץ. הפניות כוללות..." (natural language answer in Hebrew)
- **Response:** Text answer + list of requests
- **Speed:** First time: ~2-5 minutes (loads model), Subsequent: ~5-15 seconds

---

### Question 2: Person Query - אור גלילי
**Query:** `פניות מאור גלילי`  
**English:** Requests from אור גלילי  
**Type:** Person query  

**Expected Results for Type 1 (חיפוש בלבד):**
- **Total Count:** 34 requests
- **Displayed:** Top 20 requests (or all 34 if less than 20)
- **Sample Request IDs:** 221000138, 221000146, 221000149, 221000161, 221000162, 221000163, 221000164, 221000178, 221000179, 221000195
- **Should find in fields:** UpdatedBy, CreatedBy, ResponsibleEmployeeName, ProjectName
- **Response:** List of requests with details

**Expected Results for Type 3 (RAG - עם תשובה מלאה):**
- **Total Count:** 34 requests
- **Displayed:** Top 20 requests (or all 34)
- **Text Answer:** "נמצאו 34 פניות של אור גלילי..." (natural language answer)
- **Response:** Text answer + list of requests

---

### Question 3: Count Query
**Query:** `כמה פניות יש מיניב ליבוביץ?`  
**English:** How many requests are from יניב ליבוביץ?  
**Type:** Count query  
**Expected Results:**
- **Count:** 225 requests
- **Expected Answer (RAG):** "נמצאו 225 פניות של יניב ליבוביץ" or similar
- **Test:** RAG should generate answer with count, search should return 225 requests

---

### Question 4: Project Query
**Query:** `פרויקט בדיקה אור גלילי`  
**English:** Project בדיקה אור גלילי  
**Type:** Project query  
**Expected Results:**
- **Count:** 27 requests
- **Sample Request IDs:** 221000146, 221000162, 221000163, 221000164, 221000178, 221000179, 221000195, 221000197, 221000200, 221000209
- **Should find in fields:** ProjectName
- **Test:** Search should return exactly 27 requests with "בדיקה אור גלילי" in ProjectName

---

### Question 5: Type Query
**Query:** `בקשות מסוג 4`  
**English:** Requests of type 4  
**Type:** Type query  
**Expected Results:**
- **Count:** 3,731 requests
- **Sample Request IDs:** 920200001, 920200009, 920200011, 920200012, 920200013, 920200014, 920200015, 920200016, 920200017, 920200018
- **Should find in fields:** RequestTypeId = 4
- **Test:** Search should return ~3,731 requests (may be limited by top_k, but should show many)

---

### Question 6: Status Query
**Query:** `בקשות בסטטוס 10`  
**English:** Requests with status 10  
**Type:** Status query  
**Expected Results:**
- **Count:** 4,217 requests
- **Sample Request IDs:** 920200001, 920200002, 920200003, 920200004, 920200005, 920200006, 920200007, 920200008, 920200009, 920200010
- **Should find in fields:** RequestStatusId = 10
- **Test:** Search should return ~4,217 requests

---

### Question 7: General Semantic Query
**Query:** `תיאום תכנון`  
**English:** Planning coordination  
**Type:** General semantic query  
**Expected Results:**
- **Count:** ~441 requests (semantic search - may vary)
- **Sample Request IDs:** 213000077, 216001192, 216001194, 216001195, 216001198, 216001199, 216001200, 216001201, 216001202, 216001204
- **Should find in fields:** ProjectName, ProjectDesc, AreaDesc (semantic match)
- **Test:** Search should find requests related to "תיאום תכנון" semantically

---

### Question 8: Person Query - אוקסנה כלפון
**Query:** `פניות מאוקסנה כלפון`  
**English:** Requests from אוקסנה כלפון  
**Type:** Person query  
**Expected Results:**
- **Count:** 186 requests
- **Sample Request IDs:** 211000002, 211000003, 211000004, 211000016, 211000026, 211000060, 211000067, 211000083, 211000153, 211000212
- **Should find in fields:** UpdatedBy, CreatedBy, ResponsibleEmployeeName
- **Test:** Search should return ~186 requests

---

### Question 9: Person Query - משה אוגלבו
**Query:** `פניות ממשה אוגלבו`  
**English:** Requests from משה אוגלבו  
**Type:** Person query  
**Expected Results:**
- **Count:** 704 requests
- **Sample Request IDs:** 211000005, 211000006, 211000007, 211000008, 211000009, 211000010, 211000011, 211000012, 211000013, 211000014
- **Should find in fields:** UpdatedBy, CreatedBy, ResponsibleEmployeeName
- **Test:** Search should return ~704 requests

---

### Question 10: Complex Query (Type + Status)
**Query:** `כמה פניות יש מסוג 4 בסטטוס 10?`  
**English:** How many requests of type 4 with status 10?  
**Type:** Complex query (multiple filters)  
**Expected Results:**
- **Count:** 3,237 requests
- **Sample Request IDs:** 920200001, 920200009, 920200011, 920200012, 920200013, 920200014, 920200015, 920200016, 920200017, 920200018
- **Should find in fields:** RequestTypeId = 4 AND RequestStatusId = 10
- **Test:** Search should return ~3,237 requests matching both criteria

---

## 🧪 How to Test

### Step 1: Test Search (Options 1 or 2)
1. Open the frontend
2. Enter one of the queries above
3. Select "חיפוש בלבד" or "RAG - רק חיפוש"
4. Click search
5. **Verify:**
   - Number of results matches expected count (or close, depending on top_k)
   - Sample Request IDs appear in results
   - Results are relevant

### Step 2: Test RAG with Answer (Option 3)
1. Enter a count query (e.g., "כמה פניות יש מיניב ליבוביץ?")
2. Select "RAG - עם תשובה מלאה"
3. Click search
4. **Verify:**
   - Answer contains the expected count
   - Answer is in Hebrew
   - List of requests is shown
   - Results match expected

### Step 3: Compare with Database
For each query, you can verify in the database:
```sql
-- Example for Question 1
SELECT COUNT(*) FROM requests 
WHERE updatedby ILIKE '%יניב ליבוביץ%' 
   OR createdby ILIKE '%יניב ליבוביץ%'
   OR responsibleemployeename ILIKE '%יניב ליבוביץ%';
```

---

## ✅ Success Criteria

**For Search (Options 1 & 2):**
- ✅ Returns relevant requests
- ✅ Count matches expected (or close)
- ✅ Sample IDs appear in results
- ✅ Results are accurate (not hallucinations)

**For RAG with Answer (Option 3):**
- ✅ Answer contains correct count
- ✅ Answer is in Hebrew
- ✅ Answer is natural and readable
- ✅ List of requests matches answer
- ✅ No hallucinations (numbers match reality)

---

## 📝 Notes

1. **Counts may vary slightly** - Database has 8,195 requests, but some may be filtered
2. **Top-K limitation** - Search may return top 20, but count should be accurate
3. **Semantic search** - General queries may find more/less than exact matches
4. **Name variations** - Some names appear in different formats (e.g., "יניב ליבוביץ" vs "ליבוביץ יניב")

---

## 🔍 Additional Test Queries

**Easy queries (should work well):**
- `פניות מיניב ליבוביץ` - 225 requests
- `בקשות מסוג 4` - 3,731 requests
- `פרויקט בדיקה אור גלילי` - 27 requests

**Medium queries:**
- `תיאום תכנון` - ~441 requests (semantic)
- `כמה פניות יש מיניב ליבוביץ?` - Count query

**Hard queries (complex):**
- `כמה פניות יש מסוג 4 בסטטוס 10?` - Multiple filters
- `פניות ממשה אוגלבו` - 704 requests (large result set)

---

**Use this guide to systematically test the system and verify accuracy!**

