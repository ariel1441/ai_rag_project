# Field Weighting - FINAL Proposal (Based on User Feedback)

## 🎯 Key Insights from Your Feedback

1. **Booleans are important for SPECIFIC queries**: "Give me requests where IsPenetrateGround = true"
   - Solution: Include them in embeddings (so semantic search can find them)
   - But lower weight (since they're not for general queries)

2. **Coordinates are useful**: "Find requests close to each other"
   - Solution: Include coordinates as text (e.g., "Area: X, Y")
   - This allows semantic search to find "close" requests

3. **RequestTypeId is very important**: Move it up in weight

4. **Contact fields are important**: ContactEmail, ContactFirstName, ContactLastName (and Yazam versions)

5. **Low coverage descriptive fields**: When not empty, they're important
   - Solution: Include them with normal weight (they're descriptive text)

---

## 📋 FINAL FIELD LIST & WEIGHTS

### 🔴 Weight 3.0x (Repeat 2-3 times - HIGHEST PRIORITY)

**Core descriptive text - what users search for most:**

1. `ProjectName` (98.9% coverage) ⭐
2. `UpdatedBy` (99.9% coverage) ⭐⭐ **CRITICAL - This is what we're missing!**
3. `ProjectDesc` (39.5% coverage)
4. `AreaDesc` (55.3% coverage)
5. `Remarks` (40.2% coverage)
6. `RequestTypeId` (100% coverage) ⭐ **MOVED UP - You said it's important!**

### 🟠 Weight 2.0x (Repeat 1-2 times - HIGH PRIORITY)

**Important identifiers and names:**

7. `CreatedBy` (88.1% coverage) ⭐⭐ **CRITICAL - This is what we're missing!**
8. `RequestStatusId` (100% coverage)
9. `RequestTypeReasonId` (39.1% coverage)
10. `ContactFirstName` (44.8% coverage) ⭐ **You said it's important!**
11. `ContactLastName` (11.3% coverage) ⭐ **You said it's important!**
12. `ContactEmail` (39.8% coverage) ⭐ **You said it's important!**
13. `ResponsibleEmployeeName` (26.6% coverage) ⭐⭐ **CRITICAL - This is what we're missing!**
14. `Yazam_ContactName` (21.3% coverage) ⭐ **You said it's important!**
15. `Yazam_ContactEmail` (21.0% coverage) ⭐ **You said it's important!**
16. `Yazam_CompanyName` (18.4% coverage)

### 🟡 Weight 1.0x (Include once - MODERATE PRIORITY)

**Supporting information:**

17. `ResponsibleOrgEntityName` (94.1% coverage)
18. `ResponsibleEmployeeRoleName` (26.6% coverage)
19. `RequestStatusDate` (100% coverage)
20. `PenetrateGroundDesc` (1.6% coverage) ⭐ **You said: when not empty, it's important!**
21. `RequestJobShortDescription` (0.5% coverage) ⭐ **You said: when not empty, it's important!**
22. `ExternalRequestStatusDesc` (8.4% coverage)
23. `PenetrateGroundTypeId` (3.5% coverage)
24. `ContactPhone` (35.3% coverage)
25. `Yazam_ContactPhone` (21.0% coverage)
26. `RequestContactTz` (11.8% coverage)
27. `PlanNum` (8.2% coverage)
28. `RequestSourceNun` (23.6% coverage)

### ⚪ Weight 0.5x (Include once - LOW PRIORITY, for SPECIFIC queries)

**Booleans and flags - important for specific queries, not general:**

29. `IsPenetrateGround` (90.5% coverage) ⭐ **You said: important to know if true/false**
30. `IsActive` (100% coverage) ⭐ **You said: kinda important to know if true/false**
31. `IsConvert` (100% coverage)
32. `IsManual` (100% coverage)
33. `IsMekorotLayer` (50.2% coverage)
34. `IsAreaFileValid` (89.6% coverage)
35. `IsMekorotTama1Layer` (8.0% coverage)
36. `IsImportentProject` (1.3% coverage)
37. `IsNewDocuments` (0.0% coverage) - Very low, but include for completeness

### 📍 Weight 0.5x (Include once - For spatial queries)

**Coordinates - for "close to each other" queries:**

38. `AreaCenterX` (23.0% coverage) ⭐ **You said: might want to check if requests are close**
39. `AreaCenterY` (23.0% coverage) ⭐
40. `ExtentMinX` (23.0% coverage) - Optional, might be redundant
41. `ExtentMinY` (23.0% coverage) - Optional, might be redundant
42. `ExtentMaxX` (23.0% coverage) - Optional, might be redundant
43. `ExtentMaxY` (23.0% coverage) - Optional, might be redundant
44. `AreaInSquare` (0.3% coverage) - Area size

**Note**: For coordinates, we'll format them as text like:
- "Area Center: X, Y"
- "Area Extent: MinX, MinY, MaxX, MaxY"
- This allows semantic search to find "close" requests

---

## 🎯 Implementation Strategy

### For General Queries (Most Common):
- High-weight fields (3.0x, 2.0x) dominate
- Descriptive text, names, types are emphasized
- Booleans/coordinates are there but low weight

### For Specific Queries (Less Common):
- User asks: "Give me requests where IsPenetrateGround = true"
- Semantic search will find them because boolean is in embedding
- Hybrid search (keyword filter) can also help

### For Spatial Queries:
- User asks: "Find requests close to area X, Y"
- Coordinates are in embedding as text
- Semantic search can find similar coordinates

---

## 📊 Summary

**Total Fields to Include: ~44 fields**

- 🔴 Weight 3.0x: 6 fields (core descriptive + RequestTypeId)
- 🟠 Weight 2.0x: 10 fields (important identifiers, names, contacts)
- 🟡 Weight 1.0x: 12 fields (supporting information)
- ⚪ Weight 0.5x: 16 fields (booleans, coordinates, flags)

**Exclude:**
- All IDs (RequestId, CompanyId, UserId, etc.) - Not semantic
- All dates (CreatedDate, UpdateDate, etc.) - Not semantic (unless you want temporal queries)
- Empty fields (Metahnen_Remarks, Kabalan_Remarks, Yazam_Remarks)
- Very low coverage non-descriptive fields

---

## ✅ Ready to Implement?

This proposal:
- ✅ Includes all fields you mentioned as important
- ✅ Moves RequestTypeId up to weight 3.0x
- ✅ Includes booleans with lower weight (for specific queries)
- ✅ Includes coordinates (for spatial queries)
- ✅ Includes contact fields with higher weight
- ✅ Includes low-coverage descriptive fields (when not empty, they're important)

**Should I proceed with implementing this?**

