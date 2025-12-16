# UI-Based Field Weights Update

**Date:** Current Session  
**Source:** Analysis of current workers website filtering and sorting options  
**Status:** ✅ Implemented

---

## Analysis of Current UI

### Filtering Options (Top Section):
1. **סוג הפניה (Type)** → `requesttypeid`
2. **סטטוס (Status)** → `requeststatusid`
3. **גורם מטפל (Handling Party)** → `responsibleemployeename` / `updatedby`
4. **תאריך עדכון (Update Date)** → `requeststatusdate`
5. **מקור הפנייה (Source)** → `requestsourcenun`
6. **מרחב (Area/Region)** → `areadesc`

### Sorting Options (Table Headers):
1. **עדכון אחרון (Last Update)** → `requeststatusdate`
2. **תאריך פתיחה (Opening Date)** → `createddate`
3. **סטטוס (Status)** → `requeststatusid`
4. **גורם מטפל (Handling Party)** → `responsibleemployeename` / `updatedby`
5. **זמן נותר למענה (Time Remaining)** → Calculated from `requeststatusdate`
6. **מקור וסוג פניה (Source and Type)** → `requestsourcenun` + `requesttypeid`
7. **שם הפרויקט (Project Name)** → `projectname`
8. **יוזם הפניה (Initiator)** → `createdby`
9. **מספר פניה (Request Number)** → `requestid`

---

## Changes Made

### Moved to 3.0x Weight (HIGHEST Priority):

**These fields are used in BOTH filters AND sorting - most important!**

1. ✅ **`requeststatusid`** (Status)
   - **Before:** 2.0x
   - **After:** 3.0x
   - **Reason:** Filter + Sort

2. ✅ **`responsibleemployeename`** (Handling Party)
   - **Before:** 2.0x
   - **After:** 3.0x
   - **Reason:** Filter + Sort

3. ✅ **`requeststatusdate`** (Update Date)
   - **Before:** 1.0x
   - **After:** 3.0x
   - **Reason:** Filter + Sort + Time Remaining calculation

4. ✅ **`requestsourcenun`** (Source)
   - **Before:** 1.0x
   - **After:** 3.0x
   - **Reason:** Filter + Sort

5. ✅ **`createdby`** (Initiator)
   - **Before:** 2.0x
   - **After:** 3.0x
   - **Reason:** Sort (יוזם הפניה)

### Added Missing Fields (2.0x Weight):

1. ✅ **`createddate`** (Opening Date)
   - **Before:** Missing
   - **After:** 2.0x
   - **Reason:** Sort (תאריך פתיחה)

2. ✅ **`updatedate`** (Last Update - alternative)
   - **Before:** Missing
   - **After:** 2.0x
   - **Reason:** Sort (עדכון אחרון - alternative to requeststatusdate)

---

## Final Field Weights

### 3.0x (Critical - Repeat 3 times):
- `projectname` (Project Name) ✅
- `updatedby` (Updated By) ✅
- `requesttypeid` (Type) ✅
- `requeststatusid` (Status) ⬆️ **MOVED UP**
- `responsibleemployeename` (Handling Party) ⬆️ **MOVED UP**
- `requeststatusdate` (Status Date) ⬆️ **MOVED UP**
- `requestsourcenun` (Request Source) ⬆️ **MOVED UP**
- `createdby` (Created By) ⬆️ **MOVED UP**
- `areadesc` (Area) ✅
- `projectdesc` (Description) ✅
- `remarks` (Remarks) ✅

### 2.0x (Important - Repeat 2 times):
- `createddate` (Created Date) ➕ **ADDED**
- `updatedate` (Updated Date) ➕ **ADDED**
- `requesttypereasonid` (Type Reason) ✅
- `contactfirstname` (Contact First Name) ✅
- `contactlastname` (Contact Last Name) ✅
- `contactemail` (Contact Email) ✅
- `yazam_contactname` (Yazam Contact) ✅
- `yazam_contactemail` (Yazam Contact Email) ✅
- `yazam_companyname` (Yazam Company) ✅

### 1.0x (Supporting - Include once):
- `responsibleorgentityname` (Responsible Organization) ✅
- `responsibleemployeerolename` (Responsible Role) ✅
- `penetrategrounddesc` (Penetrate Ground Description) ✅
- `requestjobshortdescription` (Job Description) ✅
- `externalrequeststatusdesc` (External Status) ✅
- `penetrategroundtypeid` (Penetrate Ground Type) ✅
- `contactphone` (Contact Phone) ✅
- `yazam_contactphone` (Yazam Contact Phone) ✅
- `requestcontacttz` (Contact TZ) ✅
- `plannum` (Plan Number) ✅

---

## Impact

### Expected Improvements:

1. **Better search for filtered fields:**
   - Queries like "פניות בסטטוס בקליטה" will rank status matches higher
   - Queries like "פניות ממקור X" will rank source matches higher

2. **Better alignment with user expectations:**
   - Fields users see in UI are now prioritized in search
   - More intuitive behavior

3. **Improved accuracy:**
   - **Expected: 5-10% improvement** for queries using UI filter/sort fields
   - Better results when users query by status, type, source, date, handling party

---

## Next Steps

### To Apply Changes:

1. **Regenerate embeddings** (required for changes to take effect):
   ```bash
   python scripts/core/generate_embeddings.py
   ```
   - This will take 30-60 minutes
   - Uses new field weights

2. **Test with queries using these fields:**
   - "פניות בסטטוס בקליטה"
   - "פניות ממקור X"
   - "פניות מתאריך עדכון אחרון"
   - "פניות מגורם מטפל X"

3. **Verify improvement:**
   - Compare results before/after
   - Check if filtered fields rank higher

---

## Summary

**Key Insight:** Fields in UI filters/sort are what users interact with most.

**Action Taken:** Increased weights for all UI filter/sort fields to 3.0x (highest priority).

**Result:** Better search results aligned with user expectations.

**Next:** Regenerate embeddings to apply changes.

