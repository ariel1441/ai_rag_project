# Scripts Organization Status ✅

## 📁 Current Structure

```
scripts/
├── core/                    # ✅ Main production scripts
│   ├── generate_embeddings.py    (CURRENT - uses old combine_text_fields)
│   └── search.py                  (CURRENT - working)
│
├── utils/                    # ✅ Shared utility modules
│   ├── __init__.py
│   ├── database.py          (Database connection helpers)
│   ├── hebrew.py            (Hebrew RTL fix, encoding setup)
│   └── text_processing.py  (combine_text_fields, chunk_text - OLD & NEW versions)
│
├── helpers/                  # ✅ Utility/helper scripts
│   ├── check_missing_fields.py
│   ├── check_hebrew_data.py
│   ├── create_env_file.py
│   ├── fix_hebrew_display.py
│   ├── fix_terminal_hebrew.bat
│   └── fix_terminal_hebrew.ps1
│
├── tests/                    # ✅ Test scripts
│   ├── analyze_search_results.py
│   ├── analyze_specific_query.py
│   ├── test_*.py (multiple test files)
│   └── verify_complete_logic.py
│
├── archive/                  # ✅ Old/legacy versions (kept for reference)
│   └── search_*.py (old search versions)
│
├── README.md                 # ✅ Documentation
└── ORGANIZATION_STATUS.md    # ✅ This file
```

## ✅ What's Done

1. **Folder Structure**: Created organized subfolders (core, utils, helpers, tests, archive)
2. **Utility Modules**: Created reusable utilities (database, hebrew, text_processing)
3. **Script Organization**: Moved scripts to appropriate folders
4. **Backup**: Current working scripts are in `core/` and `archive/`

## ⚠️ What's Next (Before Improving Embeddings)

1. **Update `core/generate_embeddings.py`**:
   - Use `utils.database.get_db_connection()` instead of manual connection
   - Use `utils.text_processing.combine_text_fields()` (currently has duplicate code)
   - Use `utils.text_processing.chunk_text()` (currently has duplicate code)

2. **Update `core/search.py`**:
   - Use `utils.database.get_db_connection()` instead of manual connection
   - Use `utils.hebrew.fix_hebrew_rtl()` instead of duplicate function
   - Use `utils.hebrew.setup_hebrew_encoding()` instead of duplicate code

3. **Improve Embeddings**:
   - Update `utils/text_processing.py` to use `combine_text_fields_weighted()` by default
   - Update `core/generate_embeddings.py` to use the weighted version
   - Regenerate embeddings

## 🎯 Ready to Start?

**YES!** The structure is organized. We can now:

1. **Option A**: Update core scripts to use utils first (cleaner, but takes a bit longer)
2. **Option B**: Go straight to improving embeddings (faster, but scripts will have some duplicate code)

**Recommendation**: Option B - Go straight to improving embeddings. We can refactor scripts to use utils later. The important thing is to improve the embeddings now.

---

## 📝 Next Steps

1. ✅ Structure organized
2. ⏳ **NEXT**: Update `combine_text_fields()` to use weighted version with all fields
3. ⏳ Regenerate embeddings
4. ⏳ Test search with improved embeddings

---

*Last Updated: After organization*

