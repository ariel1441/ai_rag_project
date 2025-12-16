# Field Weights Based on Current UI Analysis

**Source:** Analysis of current workers website filtering and sorting options

---

## Current UI Analysis

### Filtering Options (Top Section):
1. **סוג הפניה (Type of Referral/Request)** → `requesttypeid`
2. **סטטוס (Status)** → `requeststatusid`
3. **גורם מטפל (Handling Party/Factor)** → `responsibleemployeename` or `updatedby`
4. **תאריך עדכון (Update Date)** → `requeststatusdate` or `updatedate`
5. **מקור הפנייה (Source of Referral/Request)** → `requestsourcenun` or similar
6. **מרחב (Area/Region)** → `areadesc` or similar

### Sorting Options (Table Headers):
1. **פניות דומות (Similar Referrals/Requests)** → Feature, not a field
2. **עדכון אחרון (Last Update)** → `requeststatusdate` or `updatedate`
3. **תאריך פתיחה (Opening Date)** → `createddate` or similar
4. **סטטוס (Status)** → `requeststatusid`
5. **גורם מטפל (Handling Party/Factor)** → `responsibleemployeename` or `updatedby`
6. **זמן נותר למענה (Time Remaining for Response)** → Calculated from `requeststatusdate`
7. **מקור וסוג פניה (Source and Type)** → `requestsourcenun` + `requesttypeid`
8. **שם הפרויקט (Project Name)** → `projectname`
9. **יוזם הפניה (Referral/Request Initiator)** → `createdby` or similar
10. **מספר פניה (Referral/Request Number)** → `requestid`

---

## Current Field Weights vs. UI Priority

### Fields in UI Filters/Sort (Should be HIGHEST Priority):

| Field | Current Weight | UI Priority | Should Be |
|-------|---------------|-------------|-----------|
| `requesttypeid` | 3.0x ✅ | **HIGH** (Filter) | 3.0x ✅ (Already correct) |
| `requeststatusid` | 2.0x ⚠️ | **HIGH** (Filter + Sort) | **3.0x** ⬆️ |
| `responsibleemployeename` | 2.0x ⚠️ | **HIGH** (Filter + Sort) | **3.0x** ⬆️ |
| `requeststatusdate` | 1.0x ❌ | **HIGH** (Filter + Sort) | **3.0x** ⬆️ |
| `requestsourcenun` | 1.0x ❌ | **HIGH** (Filter + Sort) | **3.0x** ⬆️ |
| `areadesc` | 3.0x ✅ | **HIGH** (Filter) | 3.0x ✅ (Already correct) |
| `projectname` | 3.0x ✅ | **HIGH** (Sort) | 3.0x ✅ (Already correct) |
| `createdby` | 2.0x ⚠️ | **HIGH** (Sort - Initiator) | **3.0x** ⬆️ |
| `updatedby` | 3.0x ✅ | **HIGH** (Sort - Handling Party) | 3.0x ✅ (Already correct) |
| `createddate` | ❌ Missing | **MEDIUM** (Sort) | **2.0x** ⬆️ |
| `updatedate` | ❌ Missing | **MEDIUM** (Sort) | **2.0x** ⬆️ |

---

## Recommended Changes

### Move to 3.0x Weight (HIGHEST Priority):

**These fields are used for BOTH filtering AND sorting - most important!**

1. **`requeststatusid`** (Status)
   - Used in: Filter + Sort
   - Current: 2.0x → Should be: **3.0x**

2. **`responsibleemployeename`** (Handling Party/Factor)
   - Used in: Filter + Sort
   - Current: 2.0x → Should be: **3.0x**

3. **`requeststatusdate`** (Update Date)
   - Used in: Filter + Sort + Time Remaining calculation
   - Current: 1.0x → Should be: **3.0x**

4. **`requestsourcenun`** (Source of Referral)
   - Used in: Filter + Sort
   - Current: 1.0x → Should be: **3.0x**

5. **`createdby`** (Initiator)
   - Used in: Sort
   - Current: 2.0x → Should be: **3.0x**

### Add Missing Fields (2.0x Weight):

1. **`createddate`** (Opening Date)
   - Used in: Sort
   - Current: Missing → Should be: **2.0x**

2. **`updatedate`** (Last Update - alternative to requeststatusdate)
   - Used in: Sort
   - Current: Missing → Should be: **2.0x**

---

## Impact Analysis

### Why This Matters:

1. **Users filter/sort by these fields most often**
   - If they're in the UI, users expect them to work well
   - Higher weight = better search results for these fields

2. **These are the "primary keys" of user interaction**
   - Status, Type, Handling Party, Date - these are what users think about
   - Should be prioritized in semantic search

3. **Better alignment with user expectations**
   - If user filters by "Status: בקליטה", search should prioritize status matches
   - Higher weight ensures these fields rank higher in results

---

## Implementation

### Update `scripts/utils/text_processing.py`:

**Move to 3.0x (critical_fields):**
- `requeststatusid` (Status)
- `responsibleemployeename` (Handling Party)
- `requeststatusdate` (Update Date)
- `requestsourcenun` (Source)
- `createdby` (Initiator)

**Add to 2.0x (important_fields):**
- `createddate` (Opening Date)
- `updatedate` (Last Update)

**Keep at 3.0x (already correct):**
- `projectname` (Project Name)
- `updatedby` (Updated By)
- `requesttypeid` (Type)
- `areadesc` (Area/Region)

---

## Expected Improvement

**Before:**
- Status, Source, Date at lower weights
- May not rank high enough in search results
- Users filtering by these might get less relevant results

**After:**
- All UI filter/sort fields at highest weights
- Better search results when users query by these fields
- More aligned with user expectations
- **Expected accuracy improvement: 5-10%** for queries using these fields

---

## Summary

**Key Insight:** Fields that appear in UI filters/sort are the most important fields for users.

**Action:** Increase weights for all UI filter/sort fields to 3.0x (highest priority).

**Impact:** Better search results, more aligned with user expectations.

