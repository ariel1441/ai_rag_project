# Test Queries Guide - Verify All Fixes

Use this guide to test the system and verify everything works correctly.

## 🎯 Quick Test Checklist

For each query, verify:
- ✅ Count is displayed correctly (not 0 when results exist)
- ✅ Count >= returned results (never less)
- ✅ Results are relevant to the query
- ✅ Multiple entity queries return FEWER results (AND logic)
- ✅ Person names don't include type/status patterns
- ✅ No errors in terminal/console

---

## 📋 Test Queries

### 1. Single Person Queries

#### Test 1.1: פניות מאור גלילי
- **Expected Count:** ~34-142 (semantic search may find more)
- **What to check:**
  - Count is displayed (not 0)
  - Count >= 20 (returned results)
  - Results contain "אור גלילי" in person fields or project name

#### Test 1.2: פניות מיניב ליבוביץ
- **Expected Count:** ~118-225 (semantic search may find more)
- **What to check:**
  - Count is displayed (not 0)
  - Count >= 20 (returned results)
  - Results contain "יניב ליבוביץ" in person fields or project name

---

### 2. Single Type Queries

#### Test 2.1: בקשות מסוג 4
- **Expected Count:** ~208-3731 (semantic search with similarity threshold)
- **What to check:**
  - Count is displayed
  - Count >= 20 (returned results)
  - All results have `requesttypeid = 4`

#### Test 2.2: בקשות מסוג 1
- **Expected Count:** ~1000-2114
- **What to check:**
  - Count is displayed
  - All results have `requesttypeid = 1`

#### Test 2.3: בקשות מסוג 3
- **Expected Count:** ~600-1339
- **What to check:**
  - Count is displayed
  - All results have `requesttypeid = 3`

---

### 3. Single Status Queries

#### Test 3.1: בקשות בסטטוס 10
- **Expected Count:** ~2000-4217
- **What to check:**
  - Count is displayed
  - Count >= 20 (returned results)
  - All results have `requeststatusid = 10`

#### Test 3.2: בקשות בסטטוס 1
- **Expected Count:** ~114-1268
- **What to check:**
  - Count is displayed
  - All results have `requeststatusid = 1`

#### Test 3.3: בקשות בסטטוס 7
- **Expected Count:** ~300-769
- **What to check:**
  - Count is displayed
  - All results have `requeststatusid = 7`

---

### 4. Multiple Entity Queries (AND Logic) ⚠️ CRITICAL TESTS

These tests verify that AND logic works correctly - multiple filters should return FEWER results.

#### Test 4.1: בקשות מאור גלילי מסוג 4
- **Expected Count:** 0 (no requests match both criteria in DB)
- **Single person count:** ~34-142
- **What to check:**
  - ✅ Count is 0 (correct - no matches)
  - ✅ Count is LESS than single person query (AND logic working)
  - ✅ No results returned

#### Test 4.2: פניות מאור גלילי בסטטוס 10
- **Expected Count:** 0 (no requests match both criteria in DB)
- **Single person count:** ~34-142
- **What to check:**
  - ✅ Count is 0 (correct - no matches)
  - ✅ Count is LESS than single person query (AND logic working)

#### Test 4.3: פניות מיניב ליבוביץ בסטטוס 1
- **Expected Count:** ~5-7 (some requests match both)
- **Single person count:** ~118-225
- **What to check:**
  - ✅ Count is displayed (5-7)
  - ✅ Count is LESS than single person query (AND logic working)
  - ✅ Results contain both "יניב ליבוביץ" AND status_id = 1

#### Test 4.4: בקשות מיניב ליבוביץ מסוג 1
- **Expected Count:** Check if > 0
- **Single person count:** ~118-225
- **What to check:**
  - ✅ Count is LESS than single person query (AND logic working)
  - ✅ Results match both person AND type

---

### 5. Edge Cases & Special Queries

#### Test 5.1: בקשה מאור גלילי (Singular)
- **Expected Count:** ~19-156 (may differ from plural)
- **What to check:**
  - ✅ Count is reasonable (not 0)
  - ✅ Results are relevant
  - ✅ Singular vs plural may return different counts (this is OK)

#### Test 5.2: תיאום תכנון (General Query)
- **Expected Count:** Some results (semantic search)
- **What to check:**
  - ✅ Should NOT be detected as person query
  - ✅ Returns semantic results related to "תיאום תכנון"
  - ✅ Intent should be "general", not "person"

#### Test 5.3: כמה פניות יש מאור גלילי?
- **Expected Count:** Should show count
- **What to check:**
  - ✅ Query type detected as "count"
  - ✅ Returns count information

#### Test 5.4: פניות דומות ל221000226
- **Expected Count:** Similar requests to ID 221000226
- **What to check:**
  - ✅ Query type detected as "similar"
  - ✅ Returns requests similar to the specified ID
  - ✅ Results are actually similar (not random)

---

## 🔍 What to Look For

### ✅ Good Signs (Everything Working)
- Count matches or is close to expected range
- Count >= returned results (never less)
- Multiple entity queries return fewer results (AND logic)
- Person names extracted correctly (no "מסוג" or "בסטטוס" in name)
- No errors in terminal/console

### ❌ Bad Signs (Issues to Report)
- Count shows 0 when results are returned
- Count < returned results
- Multiple entity queries return MORE results (AND logic broken)
- Person names include type/status patterns
- Errors in terminal/console
- Results not relevant to query

---

## 📊 Expected Behavior Summary

| Query Type | Expected Behavior |
|------------|-------------------|
| Single Person | Returns relevant results, count displayed correctly |
| Single Type | Returns all requests of that type (with similarity threshold) |
| Single Status | Returns all requests of that status (with similarity threshold) |
| Multiple (Person + Type) | Returns FEWER results (AND logic), count <= single person count |
| Multiple (Person + Status) | Returns FEWER results (AND logic), count <= single person count |
| General Query | Semantic search, not detected as person |
| Count Query | Returns count information |
| Similar Query | Returns similar requests |

---

## 🚨 Critical Tests (Must Pass)

1. **Count Accuracy:** "פניות מיניב ליבוביץ" should show count > 0 (not 0)
2. **AND Logic:** "בקשות מאור גלילי מסוג 4" should return 0 (fewer than single person)
3. **Person Extraction:** "פניות מיניב ליבוביץ בסטטוס 1" - person name should be "יניב ליבוביץ" (not "יניב ליבוביץ בסטטוס")
4. **No Errors:** All queries should execute without errors

---

## 📝 Notes

- **Semantic Search:** Counts may differ from exact SQL LIKE queries because semantic search finds similar meanings, not just exact text matches
- **Similarity Threshold:** Applied to filter low-relevance results (0.5 for person/project, 0.4 for general, 0.2 for multiple entities with strict filters)
- **AND Logic:** When multiple entities are present, ALL must match (not OR)
- **Count vs Results:** Count is total matching requests, returned results are limited to top 20

---

## ✅ Final Verification

After testing all queries, verify:
- [ ] All single entity queries work
- [ ] All multiple entity queries return fewer results (AND logic)
- [ ] Counts are always >= returned results
- [ ] No count shows 0 when results exist
- [ ] Person names extracted correctly
- [ ] No errors in console/terminal

If all checks pass, the system is working correctly! 🎉

