# Field Weighting Proposal for Embeddings

## 📊 Analysis Summary

**Total Fields**: 83
- 🔴 **Critical**: 9 fields
- 🟠 **Important**: 31 fields  
- 🟡 **Supporting**: 28 fields
- ⚪ **Low Priority**: 15 fields

---

## 🎯 My Recommendations

### 🔴 CRITICAL Fields (Weight: 3.0x - Repeat 2-3 times)

**These are the core descriptive text fields - the main content of requests.**

| Field | Non-Null | Distinct | Recommendation | Reason |
|-------|----------|----------|----------------|--------|
| `projectname` | 1,148 | 784 | ✅ **INCLUDE (3x)** | Main project identifier - very important |
| `projectdesc` | 849 | 574 | ✅ **INCLUDE (3x)** | Project description - core content |
| `areadesc` | 313 | 213 | ✅ **INCLUDE (3x)** | Area description - important context |
| `remarks` | 166 | 95 | ✅ **INCLUDE (3x)** | Additional remarks - useful context |
| `requestjobshortdescription` | 6 | 2 | ⚠️ **INCLUDE (1x)** | Very few values - lower weight |
| `penetrategrounddesc` | 40 | 13 | ✅ **INCLUDE (2x)** | Specific description - moderate importance |
| `metahnen_remarks` | 0 | 0 | ❌ **EXCLUDE** | No data |
| `kabalan_remarks` | 0 | 0 | ❌ **EXCLUDE** | No data |
| `yazam_remarks` | 0 | 0 | ❌ **EXCLUDE** | No data |

**Decision**: Include 6 fields (exclude 3 empty ones)

---

### 🟠 IMPORTANT Fields (Weight: 2.0x - Repeat 1-2 times)

**These are names, contacts, responsible people, status/type info.**

#### Status & Type Fields
| Field | Non-Null | Distinct | Recommendation |
|-------|----------|----------|----------------|
| `requesttypeid` | 1,175 | 6 | ✅ **INCLUDE (2x)** - Very important for categorization |
| `requesttypereasonid` | 1,050 | 32 | ✅ **INCLUDE (2x)** - Important for categorization |
| `requeststatusid` | 1,175 | 14 | ✅ **INCLUDE (2x)** - Important for status |
| `requeststatusdate` | 1,175 | 1,137 | ⚠️ **INCLUDE (1x)** - Date, less semantic value |
| `penetrategroundtypeid` | 58 | 7 | ✅ **INCLUDE (1x)** - Low coverage |
| `externalrequeststatusdesc` | 125 | 4 | ✅ **INCLUDE (1x)** - Low coverage |

#### People & Contacts (HIGH PRIORITY - These are what we're missing!)
| Field | Non-Null | Distinct | Recommendation |
|-------|----------|----------|----------------|
| `updatedby` | 1,173 | 44 | ✅ **INCLUDE (2x)** - **CRITICAL!** This is what we're missing! |
| `createdby` | 1,057 | 28 | ✅ **INCLUDE (2x)** - **CRITICAL!** This is what we're missing! |
| `responsibleemployeename` | 874 | 35 | ✅ **INCLUDE (2x)** - **CRITICAL!** Important for search |
| `responsibleemployeerolename` | 874 | 3 | ✅ **INCLUDE (1x)** - Lower distinct count |
| `contactfirstname` | 725 | 101 | ✅ **INCLUDE (2x)** - Important for search |
| `contactlastname` | 358 | 20 | ✅ **INCLUDE (1x)** - Lower coverage |
| `contactemail` | 1,025 | 72 | ✅ **INCLUDE (1x)** - Email, less semantic |
| `contactphone` | 564 | 57 | ⚠️ **INCLUDE (0.5x)** - Phone numbers, very low semantic value |

#### Organizations
| Field | Non-Null | Distinct | Recommendation |
|-------|----------|----------|----------------|
| `responsibleorgentityname` | 1,019 | 7 | ✅ **INCLUDE (1x)** - Organization name |
| `responsibleorgentityid` | 1,019 | 5 | ❌ **EXCLUDE** - ID, not semantic |
| `responsibleuserid` | 874 | 35 | ❌ **EXCLUDE** - ID, not semantic |

#### Metahnen Contacts
| Field | Non-Null | Distinct | Recommendation |
|-------|----------|----------|----------------|
| `metahnen_companyname` | 37 | 16 | ✅ **INCLUDE (1x)** - Low coverage |
| `metahnen_contactname` | 37 | 15 | ✅ **INCLUDE (1x)** - Low coverage |
| `metahnen_contactemail` | 35 | 12 | ⚠️ **INCLUDE (0.5x)** - Very low coverage |
| `metahnen_contactphone` | 35 | 16 | ❌ **EXCLUDE** - Very low coverage + phone |

#### Kabalan Contacts
| Field | Non-Null | Distinct | Recommendation |
|-------|----------|----------|----------------|
| `kabalan_companyname` | 52 | 25 | ✅ **INCLUDE (1x)** - Low coverage |
| `kabalan_contactname` | 85 | 42 | ✅ **INCLUDE (1x)** - Moderate coverage |
| `kabalan_contactemail` | 47 | 18 | ⚠️ **INCLUDE (0.5x)** - Low coverage |
| `kabalan_contactphone` | 45 | 24 | ❌ **EXCLUDE** - Low coverage + phone |

#### Yazam Contacts
| Field | Non-Null | Distinct | Recommendation |
|-------|----------|----------|----------------|
| `yazam_companyname` | 245 | 29 | ✅ **INCLUDE (1x)** - Moderate coverage |
| `yazam_contactname` | 283 | 43 | ✅ **INCLUDE (1x)** - Moderate coverage |
| `yazam_contactemail` | 277 | 33 | ⚠️ **INCLUDE (0.5x)** - Moderate coverage |
| `yazam_contactphone` | 271 | 43 | ❌ **EXCLUDE** - Phone numbers |

#### Other
| Field | Non-Null | Distinct | Recommendation |
|-------|----------|----------|----------------|
| `requestcontacttz` | 159 | 14 | ⚠️ **INCLUDE (0.5x)** - Tax ID, low semantic |
| `prestatutoryproceduretype` | 6 | 1 | ❌ **EXCLUDE** - Very low coverage |

**Decision**: Include ~20 fields (exclude IDs, phones, very low coverage)

---

### 🟡 SUPPORTING Fields (Weight: 1.0x - Include once)

**These are IDs, numbers, dates, metadata.**

#### IDs (Most should be EXCLUDED - not semantic)
| Field | Non-Null | Distinct | Recommendation |
|-------|----------|----------|----------------|
| `requestid` | 1,175 | 1,175 | ❌ **EXCLUDE** - Internal ID, not semantic |
| `externaluserid` | 357 | 25 | ❌ **EXCLUDE** - ID |
| `companyid` | 530 | 100 | ❌ **EXCLUDE** - ID |
| `usercompanyroleid` | 388 | 6 | ❌ **EXCLUDE** - ID |
| `requestsourceid` | 1,175 | 9 | ⚠️ **INCLUDE (0.5x)** - Low distinct, but might be useful |
| `planningauthorityid` | 16 | 11 | ❌ **EXCLUDE** - ID + low coverage |
| `metahnen_companyid` | 20 | 6 | ❌ **EXCLUDE** - ID |
| `kabalan_companyid` | 17 | 6 | ❌ **EXCLUDE** - ID |
| `yazam_companyid` | 179 | 10 | ❌ **EXCLUDE** - ID |
| `externalrequestid` | 127 | 105 | ❌ **EXCLUDE** - ID |
| `previousrequestid` | 7 | 7 | ❌ **EXCLUDE** - ID + very low coverage |
| `requestconditionid` | 4 | 2 | ❌ **EXCLUDE** - ID + very low coverage |
| `projectid` | 22 | 3 | ❌ **EXCLUDE** - ID |
| `createduserid` | 973 | 18 | ❌ **EXCLUDE** - ID |
| `updateduserid` | 1,102 | 33 | ❌ **EXCLUDE** - ID |

#### Numbers & References (Some might be useful)
| Field | Non-Null | Distinct | Recommendation |
|-------|----------|----------|----------------|
| `requestsourcenun` | 263 | 260 | ⚠️ **INCLUDE (0.5x)** - Source number, might be useful |
| `referencenum` | 39 | 26 | ⚠️ **INCLUDE (0.5x)** - Reference number |
| `plannum` | 46 | 40 | ✅ **INCLUDE (1x)** - Plan number, might be searched |
| `projectnumber` | 22 | 5 | ⚠️ **INCLUDE (0.5x)** - Low coverage |
| `nummainprogramnum` | 1 | 1 | ❌ **EXCLUDE** - Very low coverage |

#### Dates (Generally not semantic, but might be useful for context)
| Field | Non-Null | Distinct | Recommendation |
|-------|----------|----------|----------------|
| `receptiondate` | 1,019 | 900 | ❌ **EXCLUDE** - Date, not semantic |
| `responsedate` | 557 | 519 | ❌ **EXCLUDE** - Date, not semantic |
| `publicationdate` | 56 | 22 | ❌ **EXCLUDE** - Date, not semantic |
| `sladate` | 1,129 | 365 | ❌ **EXCLUDE** - Date, not semantic |
| `createddate` | 1,175 | 1,108 | ❌ **EXCLUDE** - Date, not semantic |
| `updatedate` | 1,175 | 1,174 | ❌ **EXCLUDE** - Date, not semantic |
| `externalrequestcreatedate` | 195 | 108 | ❌ **EXCLUDE** - Date, not semantic |

#### Flags
| Field | Non-Null | Distinct | Recommendation |
|-------|----------|----------|----------------|
| `isareafilevalid` | 837 | 2 | ⚠️ **INCLUDE (0.5x)** - Boolean flag, low semantic |

**Decision**: Include ~3-5 fields (mostly exclude IDs and dates)

---

### ⚪ LOW PRIORITY Fields (Weight: 0.5x - Include once, optional)

**These are coordinates, flags, technical fields.**

| Field | Non-Null | Distinct | Recommendation |
|-------|----------|----------|----------------|
| `ispenetrateground` | 980 | 2 | ⚠️ **INCLUDE (0.5x)** - Boolean flag |
| `areacenterx` | 525 | 105 | ❌ **EXCLUDE** - Coordinate, not semantic |
| `areacentery` | 525 | 103 | ❌ **EXCLUDE** - Coordinate, not semantic |
| `extentminx` | 525 | 103 | ❌ **EXCLUDE** - Coordinate, not semantic |
| `extentminy` | 525 | 102 | ❌ **EXCLUDE** - Coordinate, not semantic |
| `extentmaxx` | 525 | 103 | ❌ **EXCLUDE** - Coordinate, not semantic |
| `extentmaxy` | 525 | 103 | ❌ **EXCLUDE** - Coordinate, not semantic |
| `ismekorotlayer` | 525 | 2 | ⚠️ **INCLUDE (0.5x)** - Boolean flag |
| `isconvert` | 1,175 | 2 | ⚠️ **INCLUDE (0.5x)** - Boolean flag |
| `ismanual` | 1,175 | 2 | ⚠️ **INCLUDE (0.5x)** - Boolean flag |
| `isactive` | 1,175 | 2 | ⚠️ **INCLUDE (0.5x)** - Boolean flag |
| `ismekorottama1layer` | 98 | 2 | ❌ **EXCLUDE** - Low coverage |
| `isnewdocuments` | 2 | 1 | ❌ **EXCLUDE** - Very low coverage |
| `isimportentproject` | 24 | 2 | ⚠️ **INCLUDE (0.5x)** - Flag, might be useful |
| `areainsquare` | 38 | 8 | ❌ **EXCLUDE** - Number, not semantic |

**Decision**: Include ~5 boolean flags, exclude all coordinates

---

## 📋 FINAL RECOMMENDATION

### ✅ INCLUDE (Total: ~35-40 fields)

#### Weight 3.0x (Repeat 2-3 times):
1. `projectname`
2. `projectdesc`
3. `areadesc`
4. `remarks`

#### Weight 2.0x (Repeat 1-2 times):
5. `requesttypeid`
6. `requesttypereasonid`
7. `requeststatusid`
8. `updatedby` ⭐ **CRITICAL - This is what we're missing!**
9. `createdby` ⭐ **CRITICAL - This is what we're missing!**
10. `responsibleemployeename` ⭐ **CRITICAL - This is what we're missing!**
11. `contactfirstname`
12. `penetrategrounddesc`

#### Weight 1.0x (Include once):
13. `requeststatusdate`
14. `penetrategroundtypeid`
15. `externalrequeststatusdesc`
16. `responsibleemployeerolename`
17. `contactlastname`
18. `contactemail`
19. `responsibleorgentityname`
20. `metahnen_companyname`
21. `metahnen_contactname`
22. `kabalan_companyname`
23. `kabalan_contactname`
24. `yazam_companyname`
25. `yazam_contactname`
26. `plannum`
27. `requestjobshortdescription`

#### Weight 0.5x (Include once, low emphasis):
28. `contactphone`
29. `metahnen_contactemail`
30. `kabalan_contactemail`
31. `yazam_contactemail`
32. `requestcontacttz`
33. `requestsourcenun`
34. `referencenum`
35. `projectnumber`
36. `isareafilevalid`
37. `ispenetrateground`
38. `ismekorotlayer`
39. `isconvert`
40. `ismanual`
41. `isactive`
42. `isimportentproject`

### ❌ EXCLUDE (~43 fields)
- All IDs (requestid, companyid, userid, etc.)
- All dates (createddate, updatedate, etc.)
- All coordinates (areacenterx, areacentery, etc.)
- Phone numbers (except main contactphone)
- Empty fields (metahnen_remarks, kabalan_remarks, yazam_remarks)
- Very low coverage fields (<10 non-null)

---

## 💡 My Reasoning

1. **Names are critical**: `updatedby`, `createdby`, `responsibleemployeename` - these are what users search for!
2. **Descriptive text is most important**: Project name, description, area, remarks - these are the core content
3. **IDs are not semantic**: They don't help with meaning-based search
4. **Dates are not semantic**: They don't help with meaning (unless we want temporal queries, but that's different)
5. **Coordinates are not semantic**: They're spatial, not textual
6. **Phone numbers have low semantic value**: Hard to search by meaning
7. **Boolean flags have some value**: But low weight since they're just true/false

---

## ❓ Questions for You

1. **Do you want to include dates?** (e.g., "requests from last month") - Currently I say NO, but we could include them as context
2. **Do you want to include coordinates?** (e.g., "requests in area X") - Currently I say NO, but if you search by location...
3. **Do you want to include all phone numbers?** - Currently only main `contactphone` included
4. **Do you want to include request IDs?** - Currently NO, but might be useful for exact matching
5. **What about very low coverage fields?** (e.g., `requestjobshortdescription` with only 6 values) - Include or exclude?

---

## 🎯 Next Steps

Once you approve this proposal, I will:
1. Update `utils/text_processing.py` with the approved field list and weights
2. Update `core/generate_embeddings.py` to use the new weighted function
3. Test with a few requests first
4. Regenerate all embeddings
5. Test search (especially "פניות מאריאל בן עקיבא")

**What do you think? Any changes you want to make?**

