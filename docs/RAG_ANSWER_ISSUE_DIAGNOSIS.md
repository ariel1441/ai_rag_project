# RAG Answer Issue - Diagnosis & Fix

## 🔍 Problem

**What you're seeing:**
- RAG query takes 32 minutes (expected on CPU)
- Answer shows a request instead of text answer
- Answer section shows request details, not natural language text

**Expected:**
- Answer should be: "נמצאו 225 פניות של אור גלילי. הפניות כוללות..."
- Instead showing: Request details (like in results list)

---

## 🔎 Possible Causes

### 1. Answer Extraction Failing

**Symptoms:**
- Model generates answer, but extraction fails
- Answer is empty or contains prompt text
- Frontend shows nothing or wrong content

**Why it happens:**
- Model output format doesn't match expected format
- `[/INST]` marker not found
- Answer extraction logic too strict

**Fix:** Better extraction logic (already added debugging)

---

### 2. Model Not Generating Answer

**Symptoms:**
- Model generates context instead of answer
- Model repeats the prompt
- Model generates request details instead of summary

**Why it happens:**
- Prompt not clear enough
- Model confused about what to generate
- CPU optimization (200 tokens) cuts off answer

**Fix:** Improve prompt clarity and structure

---

### 3. Frontend Display Issue

**Symptoms:**
- Answer is generated correctly, but frontend shows wrong thing
- Answer section shows first request instead of text

**Why it happens:**
- Answer is empty, frontend falls back to showing requests
- Answer contains request ID instead of text
- Display logic error

**Fix:** Check frontend logic (looks correct, but verify)

---

## 🎯 Most Likely Issue

Based on your description ("shows a request"), I suspect:

1. **Answer is empty or very short** (extraction failed)
2. **Model generated request details** instead of summary (prompt issue)
3. **Frontend shows first request** when answer is empty (fallback behavior)

**Why this happens:**
- CPU optimization: 200 tokens max, greedy decoding
- Model might generate: "פנייה מספר 221000164: פרויקט בדיקה אור גלילי..." (request details)
- Instead of: "נמצאו 225 פניות של אור גלילי..." (summary)

---

## ✅ Fixes Applied

### 1. Enhanced Answer Extraction
- Multiple extraction methods ([/INST], Answer:, token difference)
- Better debugging (shows full output)
- Warns if answer is empty/short

### 2. Improved Prompt
- Clearer instructions
- Better Hebrew formatting
- Query-type-specific prompts

### 3. Better Debugging
- Logs answer preview in terminal
- Shows extraction method used
- Warns if answer is malformed

---

## 🔧 Next Steps to Diagnose

1. **Check terminal logs** - Will show:
   - Full model output
   - Extraction method used
   - Answer preview
   - Warnings if empty

2. **Check browser console** - Will show:
   - What `data.answer` contains
   - If answer is empty/null

3. **Test with simpler query** - Try:
   - "כמה פניות יש מאור גלילי?" (count query)
   - Should generate: "נמצאו X פניות..."

---

## 💡 Expected Behavior

**Good answer:**
```
תשובה: נמצאו 225 פניות של אור גלילי. הפניות כוללות פרויקטים שונים כמו בנית בנין C1, פרויקט בדיקה, ועוד. רוב הפניות נמצאות בסטטוס פעיל.
```

**Bad answer (what you're seeing):**
```
תשובה: פנייה מספר 221000164: פרויקט בדיקה אור גלילי | עודכן על ידי: מערכת...
```

**Empty answer:**
```
תשובה: (empty or shows first request)
```

---

## 🎯 Root Cause Hypothesis

**Most likely:** Model is generating request details instead of summary because:
1. Prompt isn't clear enough about what to generate
2. Context formatting makes model think it should list requests
3. 200 token limit cuts off before summary is complete
4. Greedy decoding makes model deterministic (less creative)

**Solution:** Improve prompt to be more explicit about generating a summary, not listing requests.

