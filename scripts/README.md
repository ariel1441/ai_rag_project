# Scripts Directory Structure

## 📁 Organization

```
scripts/
├── core/              # Main production scripts (use these in production)
│   ├── generate_embeddings.py
│   └── search.py
│
├── utils/             # Shared utility modules (imported by other scripts)
│   ├── __init__.py
│   ├── database.py    # Database connection helpers
│   ├── hebrew.py      # Hebrew text utilities (RTL fix, etc.)
│   └── text_processing.py  # Text processing utilities
│
├── helpers/           # Utility/helper scripts (standalone tools)
│   ├── check_missing_fields.py
│   ├── check_hebrew_data.py
│   └── create_env_file.py
│
├── tests/             # Test scripts (for debugging/validation)
│   ├── test_*.py
│   └── verify_*.py
│
└── archive/           # Old/legacy versions (kept for reference)
    └── search_*.py (old versions)
```

## 🎯 Usage

### Production Scripts (core/)
- **`core/generate_embeddings.py`**: Generate embeddings from database
- **`core/search.py`**: Main search script (hybrid search)

### Utilities (utils/)
Import these in your scripts:
```python
from utils.database import get_db_connection
from utils.hebrew import fix_hebrew_rtl
from utils.text_processing import combine_text_fields, chunk_text
```

### Helpers (helpers/)
Run standalone:
```bash
python helpers/check_missing_fields.py
```

### Tests (tests/)
For debugging/validation:
```bash
python tests/test_similarity_search.py
```

## 📝 Migration Notes

- Old scripts moved to `archive/` for reference
- Common functions extracted to `utils/`
- Production scripts updated to use `utils/`

