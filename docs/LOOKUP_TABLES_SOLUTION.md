# Lookup Tables & Reference Data - Solution Guide

## 📋 Problem Statement

**Current Issue:**
- Many fields in the database store **IDs** (e.g., `requesttypeid = 4`)
- The actual **descriptive values** (e.g., "Type 4 = Planning Request" or "תכנון") are stored in separate lookup/reference tables
- Embeddings currently include "Type: 4" which is **not meaningful** for semantic search
- Users search for **"תכנון"** (planning), not **"4"**

**Impact:**
- Semantic search can't find requests by type name (only by ID)
- Search quality is reduced
- User experience suffers

---

## 🎯 Solution Overview

### For THIS Project (Now):
1. **Manual lookup mapping** - Create a mapping file with ID → Name
2. **Join during embedding generation** - Include both ID and name in embeddings
3. **Update text processing** - Replace IDs with names in embeddings

### For FUTURE Projects (Automatic/Smart):
1. **Auto-detect foreign keys** - Identify ID fields that reference lookup tables
2. **Auto-discover lookup tables** - Find tables with ID → Name mappings
3. **Auto-join during embedding** - Automatically include descriptive values
4. **Configurable mapping** - Allow manual override if needed

---

## 1. Solution for THIS Project (Now)

### Step 1: Create Lookup Mapping File

**File:** `config/lookup_mappings.json`

```json
{
  "requesttypeid": {
    "1": "Type 1 Name (Hebrew)",
    "2": "Type 2 Name (Hebrew)",
    "4": "תכנון",
    "5": "Type 5 Name (Hebrew)",
    "6": "Type 6 Name (Hebrew)"
  },
  "requeststatusid": {
    "1": "Status 1 Name (Hebrew)",
    "4": "Status 4 Name (Hebrew)",
    "8": "Status 8 Name (Hebrew)",
    "9": "Status 9 Name (Hebrew)",
    "10": "Status 10 Name (Hebrew)",
    "12": "Status 12 Name (Hebrew)"
  },
  "requesttypereasonid": {
    "1": "Reason 1 Name (Hebrew)",
    "3": "Reason 3 Name (Hebrew)",
    "4": "Reason 4 Name (Hebrew)",
    "11": "Reason 11 Name (Hebrew)",
    "16": "Reason 16 Name (Hebrew)"
  }
}
```

**How to get the mappings:**
1. Check original SQL Server database for lookup tables
2. Export lookup tables to CSV
3. Create mapping file manually
4. OR query the original database if accessible

### Step 2: Update Text Processing Function

**File:** `scripts/utils/text_processing.py`

**Add function to load lookup mappings:**
```python
import json
from pathlib import Path

def load_lookup_mappings() -> Dict[str, Dict[str, str]]:
    """Load lookup mappings from config file."""
    config_path = Path(__file__).parent.parent / "config" / "lookup_mappings.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_lookup_value(field_name: str, field_value: str, mappings: Dict) -> str:
    """Get descriptive value from lookup mapping."""
    if field_name in mappings and field_value in mappings[field_name]:
        return mappings[field_name][field_value]
    return field_value  # Return original if no mapping found
```

**Update `combine_text_fields_weighted()` function:**
```python
def combine_text_fields_weighted(request: Dict, lookup_mappings: Dict = None) -> str:
    """Combine text fields with weighting and lookup values."""
    if lookup_mappings is None:
        lookup_mappings = load_lookup_mappings()
    
    # ... existing code ...
    
    # When adding requesttypeid:
    requesttypeid = get_value('requesttypeid')
    if requesttypeid:
        # Get descriptive name from lookup
        type_name = get_lookup_value('requesttypeid', requesttypeid, lookup_mappings)
        # Include both ID and name for better search
        for _ in range(3):
            fields.append(f"Type: {type_name} (ID: {requesttypeid})")
    
    # Same for requeststatusid:
    requeststatusid = get_value('requeststatusid')
    if requeststatusid:
        status_name = get_lookup_value('requeststatusid', requeststatusid, lookup_mappings)
        for _ in range(2):
            fields.append(f"Status: {status_name} (ID: {requeststatusid})")
    
    # ... rest of function ...
```

### Step 3: Regenerate Embeddings

**After updating the function:**
```bash
python scripts/core/generate_embeddings.py
```

**Result:**
- Embeddings will include "Type: תכנון (ID: 4)" instead of just "Type: 4"
- Semantic search can now find requests by type name
- Users can search "תכנון" and find type 4 requests

### Step 4: Update Query Parser (Optional)

**File:** `config/search_config.json`

**Add type name mappings:**
```json
{
  "field_mappings": {
    "תכנון": "requesttypeid",
    "תכנון": "requesttypeid",
    // ... existing mappings
  },
  "type_name_mappings": {
    "תכנון": "4",
    "בנייה": "1",
    // ... map Hebrew names to IDs
  }
}
```

**Update query parser to:**
1. Detect type name in query (e.g., "תכנון")
2. Map to ID (e.g., "4")
3. Use ID for filtering

---

## 2. Solution for FUTURE Projects (Automatic/Smart)

### Architecture: Auto-Discovery System

**Goal:** Automatically detect and use lookup tables without manual configuration

### Step 1: Auto-Detect Foreign Keys

**File:** `scripts/utils/lookup_detector.py` (NEW)

```python
"""
Auto-detect lookup tables and foreign key relationships.
"""
import psycopg2
from typing import Dict, List, Tuple

class LookupDetector:
    """Automatically detect lookup tables and mappings."""
    
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
    
    def detect_foreign_keys(self, main_table: str) -> List[Dict]:
        """
        Detect foreign key relationships from main table.
        
        Returns:
            List of {field_name, referenced_table, referenced_column}
        """
        query = """
            SELECT
                kcu.column_name as field_name,
                ccu.table_name as referenced_table,
                ccu.column_name as referenced_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_name = %s
        """
        self.cursor.execute(query, (main_table,))
        return [
            {
                'field_name': row[0],
                'referenced_table': row[1],
                'referenced_column': row[2]
            }
            for row in self.cursor.fetchall()
        ]
    
    def detect_lookup_tables(self) -> List[str]:
        """
        Detect potential lookup tables.
        
        Criteria:
        - Small number of rows (< 1000)
        - Has ID column and Name/Description column
        - Common patterns: *_types, *_statuses, *_lookup, *_ref
        """
        query = """
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name 
                    AND (column_name LIKE '%id%' OR column_name LIKE '%Id%')) as id_cols,
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_name = t.table_name 
                    AND (column_name LIKE '%name%' OR column_name LIKE '%Name%' 
                         OR column_name LIKE '%desc%' OR column_name LIKE '%Desc%'
                         OR column_name LIKE '%title%' OR column_name LIKE '%Title%')) as name_cols
            FROM information_schema.tables t
            WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
        """
        self.cursor.execute(query)
        potential_lookups = []
        
        for table_name, id_cols, name_cols in self.cursor.fetchall():
            # Check row count
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = self.cursor.fetchone()[0]
            
            # Check if it looks like a lookup table
            if (row_count < 1000 and 
                id_cols > 0 and 
                name_cols > 0 and
                (table_name.lower().endswith('_types') or
                 table_name.lower().endswith('_statuses') or
                 table_name.lower().endswith('_lookup') or
                 table_name.lower().endswith('_ref') or
                 'type' in table_name.lower() or
                 'status' in table_name.lower())):
                potential_lookups.append(table_name)
        
        return potential_lookups
    
    def build_lookup_mapping(self, lookup_table: str, id_column: str, name_column: str) -> Dict[str, str]:
        """
        Build ID → Name mapping from lookup table.
        
        Args:
            lookup_table: Name of lookup table
            id_column: Column with IDs
            name_column: Column with names/descriptions
        
        Returns:
            Dictionary mapping ID → Name
        """
        query = f"SELECT {id_column}, {name_column} FROM {lookup_table}"
        self.cursor.execute(query)
        return {str(row[0]): str(row[1]) for row in self.cursor.fetchall()}
    
    def auto_detect_all_mappings(self, main_table: str) -> Dict[str, Dict[str, str]]:
        """
        Automatically detect all lookup mappings for main table.
        
        Returns:
            Dictionary: {field_name: {id: name, ...}, ...}
        """
        mappings = {}
        
        # Detect foreign keys
        foreign_keys = self.detect_foreign_keys(main_table)
        
        for fk in foreign_keys:
            field_name = fk['field_name']
            ref_table = fk['referenced_table']
            
            # Try to find ID and Name columns in referenced table
            self.cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{ref_table}'
                ORDER BY ordinal_position
            """)
            columns = [row[0] for row in self.cursor.fetchall()]
            
            # Find ID column (usually first or contains 'id')
            id_col = None
            for col in columns:
                if 'id' in col.lower() and (col.lower().endswith('id') or col == 'id'):
                    id_col = col
                    break
            
            # Find Name/Description column
            name_col = None
            for col in columns:
                if any(keyword in col.lower() for keyword in ['name', 'desc', 'title', 'label', 'text']):
                    name_col = col
                    break
            
            if id_col and name_col:
                mappings[field_name] = self.build_lookup_mapping(ref_table, id_col, name_col)
        
        return mappings
```

### Step 2: Auto-Apply During Embedding Generation

**File:** `scripts/core/generate_embeddings.py`

**Update to use auto-detection:**
```python
from utils.lookup_detector import LookupDetector

def main():
    # ... existing code ...
    
    # Auto-detect lookup mappings
    print("Step 5: Auto-detecting lookup tables...")
    detector = LookupDetector(conn)
    lookup_mappings = detector.auto_detect_all_mappings('requests')
    
    if lookup_mappings:
        print(f"✓ Found {len(lookup_mappings)} lookup mappings:")
        for field_name, mapping in lookup_mappings.items():
            print(f"  - {field_name}: {len(mapping)} values")
    else:
        print("⚠ No lookup tables detected, using IDs only")
    
    # ... existing code ...
    
    # Use lookup mappings in text processing
    combined_text = combine_text_fields_weighted(req, lookup_mappings=lookup_mappings)
```

### Step 3: Configurable Override

**File:** `config/lookup_config.json`

```json
{
  "auto_detect": true,
  "manual_mappings": {
    "requesttypeid": {
      "table": "request_types",
      "id_column": "type_id",
      "name_column": "type_name_hebrew"
    }
  },
  "exclude_fields": [
    "companyid",
    "userid"
  ]
}
```

**Benefits:**
- ✅ Automatic detection works for most cases
- ✅ Manual override for special cases
- ✅ Exclude fields that shouldn't use lookups
- ✅ Works for any database schema

---

## 3. Implementation Priority

### For THIS Project (High Priority):

**Quick Win (1-2 hours):**
1. ✅ Create `config/lookup_mappings.json` with manual mappings
2. ✅ Update `combine_text_fields_weighted()` to use mappings
3. ✅ Regenerate embeddings
4. ✅ Test search with type names

**Result:** Search works with type names immediately

### For FUTURE Projects (Medium Priority):

**Smart System (1-2 days):**
1. ✅ Build `LookupDetector` class
2. ✅ Auto-detect foreign keys
3. ✅ Auto-detect lookup tables
4. ✅ Auto-build mappings
5. ✅ Integrate into embedding generation
6. ✅ Add configurable overrides

**Result:** Works automatically for any new project

---

## 4. Example: Before vs After

### Before (Current):
```
Embedding includes:
"Type: 4 | Status: 10 | Project: בנית בנין C1"

User searches: "תכנון" (planning)
→ No results (4 is not "תכנון")
```

### After (With Lookup):
```
Embedding includes:
"Type: תכנון (ID: 4) | Status: מאושר (ID: 10) | Project: בנית בנין C1"

User searches: "תכנון" (planning)
→ Finds all type 4 requests ✅
```

---

## 5. Files to Create/Modify

### For THIS Project:

1. **Create:** `config/lookup_mappings.json`
   - Manual ID → Name mappings

2. **Modify:** `scripts/utils/text_processing.py`
   - Add `load_lookup_mappings()` function
   - Add `get_lookup_value()` function
   - Update `combine_text_fields_weighted()` to use mappings

3. **Run:** `python scripts/core/generate_embeddings.py`
   - Regenerate embeddings with lookup values

### For FUTURE Projects:

1. **Create:** `scripts/utils/lookup_detector.py`
   - Auto-detection system

2. **Create:** `config/lookup_config.json`
   - Configuration for auto-detection

3. **Modify:** `scripts/core/generate_embeddings.py`
   - Use auto-detection

4. **Modify:** `scripts/utils/text_processing.py`
   - Support auto-detected mappings

---

## 6. Testing

### Test Cases:

1. **Search by type name:**
   - Query: "תכנון"
   - Expected: Finds all type 4 requests

2. **Search by status name:**
   - Query: "מאושר"
   - Expected: Finds all status 10 requests

3. **Search by ID (still works):**
   - Query: "מסוג 4"
   - Expected: Finds all type 4 requests

4. **Combined search:**
   - Query: "תכנון מאושר"
   - Expected: Finds type 4 + status 10 requests

---

## 7. Benefits

### Immediate Benefits (This Project):
- ✅ Better search quality
- ✅ Users can search by meaningful names
- ✅ More intuitive user experience
- ✅ Better semantic understanding

### Long-term Benefits (Future Projects):
- ✅ Automatic for any database
- ✅ No manual configuration needed
- ✅ Works with any schema
- ✅ Scalable solution

---

## 8. Next Steps

### For THIS Project:
1. **Get lookup table data** from original SQL Server database
2. **Create mapping file** (`config/lookup_mappings.json`)
3. **Update text processing** to use mappings
4. **Regenerate embeddings**
5. **Test search** with type/status names

### For FUTURE Projects:
1. **Build auto-detection system** (`lookup_detector.py`)
2. **Integrate into embedding generation**
3. **Add configuration options**
4. **Test with multiple database schemas**

---

**Last Updated:** Current Session  
**Status:** Solution designed, ready for implementation

