# Embedding Generation Setup Guide - Multi-Client Script

## 🎯 Goal

Create a reusable script that can be run on any new PC for any client to automatically:
1. Detect database schema
2. Generate configuration with defaults
3. Allow user customization
4. Generate embeddings from scratch

---

## 📋 What Stays the Same (Generic Code)

### ✅ Core Functions (No Changes Needed)

1. **Text Chunking** (`chunk_text()`)
   - Generic logic for splitting text
   - Only parameters change (size, overlap)

2. **Embedding Generation** (`model.encode()`)
   - Generic SentenceTransformer usage
   - Only model name changes

3. **Database Operations**
   - Vector table creation (generic structure)
   - Batch inserts (generic pattern)
   - Index creation (generic SQL)

4. **Pipeline Flow**
   - Load data → Combine → Chunk → Embed → Store
   - Same for every project

---

## 🔧 What Needs User Input (Parameters/Config)

### Required Parameters (Must Provide)

1. **Database Connection**
   - Host, Port, Database, User, Password
   - Source: `.env` file or command-line args

2. **Source Table Name**
   - Which table to read from
   - Example: `requests`, `products`, `documents`

3. **Primary Key Column**
   - Foreign key for embeddings table
   - Example: `requestid`, `productid`, `documentid`

### Optional Parameters (Can Auto-Detect or Use Defaults)

1. **Fields to Include**
   - Can auto-detect all columns
   - User can specify which to include/exclude

2. **Field Weights**
   - Default: All fields 1.0x
   - User can specify weights (3.0x, 2.0x, 1.0x)

3. **Chunking Parameters**
   - Default: size=512, overlap=50
   - User can override

4. **Model Choice**
   - Default: `all-MiniLM-L6-v2` (384 dims)
   - User can choose different model

5. **Vector Table Name**
   - Default: `{source_table}_embeddings`
   - User can override

---

## 🚀 Implementation Guide

### Step 1: Create Configuration File Structure

**File: `config/embedding_config.json`**

```json
{
  "database": {
    "host": "localhost",
    "port": 5433,
    "database": "ai_requests_db",
    "user": "postgres",
    "password": "${POSTGRES_PASSWORD}"
  },
  "source": {
    "table_name": "requests",
    "primary_key": "requestid",
    "limit": null
  },
  "fields": {
    "include_all": true,
    "exclude": ["id", "created_at", "updated_at"],
    "weights": {
      "3.0x": [
        "projectname",
        "updatedby",
        "requesttypeid",
        "requeststatusid"
      ],
      "2.0x": [
        "createddate",
        "updatedate",
        "contactfirstname",
        "contactlastname"
      ],
      "1.0x": [
        "projectdesc",
        "remarks",
        "areadesc"
      ]
    },
    "labels": {
      "projectname": "Project",
      "updatedby": "Updated By",
      "requesttypeid": "Type"
    }
  },
  "chunking": {
    "max_chunk_size": 512,
    "overlap": 50
  },
  "embedding": {
    "model": "sentence-transformers/all-MiniLM-L6-v2",
    "dimension": 384,
    "batch_size": 32,
    "normalize": true
  },
  "output": {
    "table_name": "request_embeddings",
    "create_index": true,
    "index_lists": null
  }
}
```

---

### Step 2: Auto-Detection Script

**File: `scripts/setup/auto_detect_schema.py`**

```python
"""
Auto-detect database schema and generate default configuration.
"""
import psycopg2
import json
from typing import Dict, List

def detect_schema(conn_config: Dict) -> Dict:
    """
    Auto-detect database schema.
    
    Returns:
        Dict with detected schema information
    """
    conn = psycopg2.connect(**conn_config)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    # For each table, get columns
    schema_info = {}
    for table in tables:
        cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """, (table,))
        
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'name': row[0],
                'type': row[1],
                'nullable': row[2] == 'YES'
            })
        
        schema_info[table] = {
            'columns': columns,
            'column_count': len(columns)
        }
    
    cursor.close()
    conn.close()
    
    return schema_info

def suggest_primary_key(columns: List[Dict]) -> str:
    """
    Suggest primary key column name.
    
    Common patterns:
    - {table}_id
    - id
    - {table}id
    """
    # Look for common patterns
    for col in columns:
        name = col['name'].lower()
        if name.endswith('_id') or name == 'id' or name.endswith('id'):
            return col['name']
    
    # Return first column as fallback
    return columns[0]['name'] if columns else 'id'

def suggest_text_fields(columns: List[Dict]) -> List[str]:
    """
    Suggest which fields are likely text fields for embeddings.
    
    Excludes:
    - IDs (ends with _id, id)
    - Dates (date, timestamp)
    - Booleans (boolean)
    - Numbers (integer, numeric)
    """
    text_fields = []
    exclude_patterns = ['_id', 'id', 'date', 'time', 'created_at', 'updated_at']
    
    for col in columns:
        name_lower = col['name'].lower()
        type_lower = col['type'].lower()
        
        # Skip if matches exclude pattern
        if any(pattern in name_lower for pattern in exclude_patterns):
            continue
        
        # Include text-like types
        if 'text' in type_lower or 'varchar' in type_lower or 'char' in type_lower:
            text_fields.append(col['name'])
        # Include if name suggests text content
        elif any(word in name_lower for word in ['name', 'desc', 'desc', 'title', 'content', 'text', 'remark', 'note']):
            text_fields.append(col['name'])
    
    return text_fields

def generate_default_config(schema_info: Dict, source_table: str) -> Dict:
    """
    Generate default configuration from detected schema.
    """
    if source_table not in schema_info:
        raise ValueError(f"Table '{source_table}' not found in database")
    
    columns = schema_info[source_table]['columns']
    primary_key = suggest_primary_key(columns)
    text_fields = suggest_text_fields(columns)
    
    # Default weights: All text fields 1.0x
    weights = {
        "3.0x": text_fields[:5] if len(text_fields) >= 5 else text_fields,  # Top 5
        "2.0x": text_fields[5:10] if len(text_fields) >= 10 else [],
        "1.0x": text_fields[10:] if len(text_fields) > 10 else []
    }
    
    config = {
        "source": {
            "table_name": source_table,
            "primary_key": primary_key
        },
        "fields": {
            "include_all": True,
            "exclude": [primary_key, "created_at", "updated_at"],
            "weights": weights,
            "labels": {field: field.replace('_', ' ').title() for field in text_fields}
        },
        "chunking": {
            "max_chunk_size": 512,
            "overlap": 50
        },
        "embedding": {
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "dimension": 384,
            "batch_size": 32,
            "normalize": True
        },
        "output": {
            "table_name": f"{source_table}_embeddings",
            "create_index": True,
            "index_lists": None  # Auto-calculate
        }
    }
    
    return config
```

---

### Step 3: Interactive Setup Wizard

**File: `scripts/setup/setup_embeddings.py`**

```python
"""
Interactive setup wizard for embedding generation.
"""
import json
import os
from pathlib import Path
from auto_detect_schema import detect_schema, generate_default_config, suggest_text_fields

def interactive_setup():
    """
    Interactive wizard to set up embedding generation.
    """
    print("=" * 70)
    print("Embedding Generation Setup Wizard")
    print("=" * 70)
    print()
    
    # Step 1: Database Connection
    print("Step 1: Database Connection")
    print("-" * 70)
    host = input("Database host [localhost]: ").strip() or "localhost"
    port = input("Database port [5433]: ").strip() or "5433"
    database = input("Database name: ").strip()
    user = input("Database user [postgres]: ").strip() or "postgres"
    password = input("Database password: ").strip()
    
    conn_config = {
        'host': host,
        'port': int(port),
        'database': database,
        'user': user,
        'password': password
    }
    
    # Step 2: Detect Schema
    print()
    print("Step 2: Detecting database schema...")
    try:
        schema_info = detect_schema(conn_config)
        print(f"✓ Found {len(schema_info)} tables")
        
        # Show tables
        print("\nAvailable tables:")
        for i, table in enumerate(schema_info.keys(), 1):
            col_count = schema_info[table]['column_count']
            print(f"  {i}. {table} ({col_count} columns)")
        
        # Step 3: Select Source Table
        print()
        print("Step 3: Select Source Table")
        print("-" * 70)
        table_choice = input("Enter table name or number: ").strip()
        
        # Handle number input
        if table_choice.isdigit():
            table_list = list(schema_info.keys())
            source_table = table_list[int(table_choice) - 1]
        else:
            source_table = table_choice
        
        if source_table not in schema_info:
            print(f"❌ Error: Table '{source_table}' not found")
            return
        
        # Step 4: Generate Default Config
        print()
        print("Step 4: Generating default configuration...")
        config = generate_default_config(schema_info, source_table)
        config['database'] = {
            'host': host,
            'port': int(port),
            'database': database,
            'user': user,
            'password': password
        }
        
        # Show detected info
        print(f"✓ Primary key detected: {config['source']['primary_key']}")
        print(f"✓ Text fields detected: {len(suggest_text_fields(schema_info[source_table]['columns']))}")
        print(f"✓ Output table: {config['output']['table_name']}")
        
        # Step 5: Customize (Optional)
        print()
        print("Step 5: Customize Configuration (Optional)")
        print("-" * 70)
        customize = input("Do you want to customize? [n]: ").strip().lower()
        
        if customize == 'y':
            # Customize chunk size
            chunk_size = input(f"Chunk size [{config['chunking']['max_chunk_size']}]: ").strip()
            if chunk_size:
                config['chunking']['max_chunk_size'] = int(chunk_size)
            
            # Customize model
            model = input(f"Model [{config['embedding']['model']}]: ").strip()
            if model:
                config['embedding']['model'] = model
                # Update dimension based on model
                if '384' in model or 'L6' in model:
                    config['embedding']['dimension'] = 384
                elif '768' in model or 'L12' in model:
                    config['embedding']['dimension'] = 768
        
        # Step 6: Save Config
        print()
        print("Step 6: Saving configuration...")
        config_path = Path("config/embedding_config.json")
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Configuration saved to: {config_path}")
        print()
        print("=" * 70)
        print("✅ Setup Complete!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Review config/embedding_config.json")
        print("  2. Customize field weights if needed")
        print("  3. Run: python scripts/core/generate_embeddings_universal.py")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    interactive_setup()
```

---

### Step 4: Universal Embedding Generation Script

**File: `scripts/core/generate_embeddings_universal.py`**

```python
"""
Universal embedding generation script.
Works with any database/table based on configuration.
"""
import json
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
from typing import Dict, List
from tqdm import tqdm
from psycopg2.extras import execute_values
from pgvector.psycopg2 import register_vector

def load_config(config_path: str = "config/embedding_config.json") -> Dict:
    """Load configuration file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Handle password from environment variable
    if config['database']['password'].startswith('${'):
        env_var = config['database']['password'][2:-1]
        config['database']['password'] = os.getenv(env_var, '')
    
    return config

def combine_fields_universal(request: Dict, config: Dict) -> str:
    """
    Combine fields based on configuration.
    Generic version that works with any schema.
    """
    fields = []
    field_config = config['fields']
    weights = field_config.get('weights', {})
    labels = field_config.get('labels', {})
    exclude = field_config.get('exclude', [])
    
    def get_value(key):
        value = request.get(key) or request.get(key.lower())
        if value is None:
            return None
        value_str = str(value).strip()
        if not value_str or value_str.upper() in ('NULL', 'NONE', ''):
            return None
        return value_str
    
    # Get all fields or specified fields
    if field_config.get('include_all', True):
        fields_to_process = [k for k in request.keys() if k not in exclude]
    else:
        fields_to_process = field_config.get('include', [])
    
    # Process fields by weight
    for field in fields_to_process:
        value = get_value(field)
        if not value:
            continue
        
        label = labels.get(field, field.replace('_', ' ').title())
        field_text = f"{label}: {value}"
        
        # Apply weight (repeat based on weight)
        weight = None
        for weight_key, weight_fields in weights.items():
            if field in weight_fields:
                weight = weight_key
                break
        
        if weight == "3.0x":
            for _ in range(3):
                fields.append(field_text)
        elif weight == "2.0x":
            for _ in range(2):
                fields.append(field_text)
        else:  # 1.0x or default
            fields.append(field_text)
    
    return " | ".join(fields) if fields else ""

def chunk_text(text: str, max_chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """Generic text chunking (same as before)."""
    if not text or len(text.strip()) == 0:
        return [""]
    
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    max_chunks = 100
    iterations = 0
    max_iterations = len(text) // (max_chunk_size - overlap) + 10
    
    while start < len(text) and iterations < max_iterations and len(chunks) < max_chunks:
        iterations += 1
        end = start + max_chunk_size
        
        if end < len(text):
            for sep in ['. ', ' | ']:
                last_sep = text.rfind(sep, start, end)
                if last_sep != -1:
                    end = last_sep + len(sep)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        next_start = end - overlap
        if next_start <= start:
            next_start = start + max_chunk_size - overlap
        
        start = next_start
        
        if start >= len(text):
            break
    
    if len(chunks) >= max_chunks:
        return [text]
    
    return chunks if chunks else [text]

def create_embeddings_table(cursor, config: Dict):
    """Create embeddings table based on configuration."""
    output_config = config['output']
    source_config = config['source']
    embedding_config = config['embedding']
    
    table_name = output_config['table_name']
    primary_key = source_config['primary_key']
    dimension = embedding_config['dimension']
    
    # Drop if exists
    cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
    
    # Create table
    cursor.execute(f"""
        CREATE TABLE {table_name} (
            id SERIAL PRIMARY KEY,
            {primary_key} VARCHAR(100) NOT NULL,
            chunk_index INTEGER DEFAULT 0,
            text_chunk TEXT NOT NULL,
            embedding vector({dimension}),
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Create indexes
    if output_config.get('create_index', True):
        # Vector index
        lists = output_config.get('index_lists')
        if not lists:
            # Auto-calculate: estimate rows, use sqrt or rows/1000
            cursor.execute(f"SELECT COUNT(*) FROM {config['source']['table_name']};")
            row_count = cursor.fetchone()[0]
            lists = max(10, min(1000, int(row_count / 1000) or 100))
        
        cursor.execute(f"""
            CREATE INDEX idx_{table_name}_vector 
            ON {table_name} 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = {lists});
        """)
        
        # Foreign key index
        cursor.execute(f"""
            CREATE INDEX idx_{table_name}_{primary_key} 
            ON {table_name}({primary_key});
        """)

def main():
    """Main embedding generation function."""
    print("=" * 70)
    print("Universal Embedding Generation")
    print("=" * 70)
    print()
    
    # Load config
    config_path = Path("config/embedding_config.json")
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        print("   Run: python scripts/setup/setup_embeddings.py")
        return 1
    
    config = load_config(str(config_path))
    
    # Connect to database
    print("Connecting to database...")
    conn = psycopg2.connect(**config['database'])
    register_vector(conn)
    cursor = conn.cursor()
    print("✓ Connected")
    
    # Create embeddings table
    print("Creating embeddings table...")
    create_embeddings_table(cursor, config)
    conn.commit()
    print("✓ Table created")
    
    # Load model
    print(f"Loading model: {config['embedding']['model']}...")
    model = SentenceTransformer(config['embedding']['model'])
    print("✓ Model loaded")
    
    # Load source data
    print(f"Loading data from {config['source']['table_name']}...")
    cursor.execute(f"SELECT * FROM {config['source']['table_name']} ORDER BY {config['source']['primary_key']};")
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    requests = [dict(zip(columns, row)) for row in rows]
    print(f"✓ Loaded {len(requests):,} rows")
    
    # Prepare documents
    print("Preparing documents...")
    documents = []
    for req in tqdm(requests, desc="Preparing"):
        primary_key = config['source']['primary_key']
        request_id = str(req.get(primary_key))
        if not request_id:
            continue
        
        combined_text = combine_fields_universal(req, config)
        chunks = chunk_text(
            combined_text,
            max_chunk_size=config['chunking']['max_chunk_size'],
            overlap=config['chunking']['overlap']
        )
        
        for chunk_idx, chunk in enumerate(chunks):
            documents.append({
                primary_key: request_id,
                'chunk_index': chunk_idx,
                'text_chunk': chunk,
                'metadata': {}  # Can add more metadata here
            })
    
    print(f"✓ Created {len(documents):,} chunks")
    
    # Generate embeddings
    print("Generating embeddings...")
    texts = [doc['text_chunk'] for doc in documents]
    embeddings = model.encode(
        texts,
        batch_size=config['embedding']['batch_size'],
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=config['embedding'].get('normalize', True)
    )
    print(f"✓ Generated {len(embeddings):,} embeddings")
    
    # Insert into database
    print("Inserting embeddings...")
    table_name = config['output']['table_name']
    primary_key = config['source']['primary_key']
    
    records = []
    for i, doc in enumerate(documents):
        embedding_str = '[' + ','.join(map(str, embeddings[i])) + ']'
        records.append((
            doc[primary_key],
            doc['chunk_index'],
            doc['text_chunk'],
            embedding_str,
            json.dumps(doc['metadata'])
        ))
    
    insert_query = f"""
        INSERT INTO {table_name} 
        ({primary_key}, chunk_index, text_chunk, embedding, metadata)
        VALUES %s
    """
    
    batch_size = 100
    for i in tqdm(range(0, len(records), batch_size), desc="Inserting"):
        batch = records[i:i+batch_size]
        execute_values(cursor, insert_query, batch)
        conn.commit()
    
    print("✓ Embeddings inserted")
    
    # Verify
    cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cursor.fetchone()[0]
    
    print()
    print("=" * 70)
    print("✅ SUCCESS!")
    print("=" * 70)
    print(f"Total embeddings: {count:,}")
    print(f"Total source rows: {len(requests):,}")
    print()
    
    cursor.close()
    conn.close()
    
    return 0

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    exit(main())
```

---

## 📝 Complete Setup Process

### For New Client/Project:

**Step 1: Run Setup Wizard**
```bash
python scripts/setup/setup_embeddings.py
```

**What it does:**
- Asks for database connection
- Auto-detects all tables
- Lets you select source table
- Auto-detects primary key
- Auto-detects text fields
- Generates default config
- Lets you customize

**Step 2: Review/Edit Config**
```bash
# Edit config/embedding_config.json
# Customize:
# - Field weights
# - Field labels
# - Chunk size
# - Model choice
```

**Step 3: Generate Embeddings**
```bash
python scripts/core/generate_embeddings_universal.py
```

**What it does:**
- Reads config
- Creates vector table
- Loads source data
- Combines fields (based on config)
- Chunks text
- Generates embeddings
- Stores in database

---

## 🎯 What Can Be Auto-Generated

### ✅ Fully Automatic (No User Input)

1. **Database Schema Detection**
   - All table names
   - All column names and types
   - Primary key suggestion

2. **Text Field Detection**
   - Identifies likely text fields
   - Excludes IDs, dates, booleans
   - Based on column names and types

3. **Default Configuration**
   - Default weights (top 5 = 3.0x, next 5 = 2.0x, rest = 1.0x)
   - Default labels (auto-format column names)
   - Default chunking (512, 50)
   - Default model (all-MiniLM-L6-v2)

4. **Index Tuning**
   - Auto-calculate `lists` parameter
   - Based on estimated row count

### ⚙️ User Can Override

1. **Field Selection**
   - Include/exclude specific fields
   - Override auto-detection

2. **Field Weights**
   - Customize 3.0x, 2.0x, 1.0x assignments
   - Add/remove fields from weight groups

3. **Field Labels**
   - Custom labels for display
   - Override auto-generated labels

4. **Chunking Parameters**
   - Chunk size (default: 512)
   - Overlap (default: 50)

5. **Model Choice**
   - Different model (changes dimension)
   - Batch size

6. **Table Names**
   - Output table name
   - Primary key column name

---

## 📁 File Structure

```
scripts/
├── setup/
│   ├── auto_detect_schema.py      # Auto-detect database schema
│   └── setup_embeddings.py        # Interactive setup wizard
├── core/
│   ├── generate_embeddings_universal.py  # Universal generation script
│   └── generate_embeddings.py     # Original (project-specific)
└── utils/
    └── text_processing.py         # Generic chunking function

config/
└── embedding_config.json          # Generated configuration

docs/
└── EMBEDDING_SETUP_GUIDE.md       # This guide
```

---

## 🔑 Key Design Decisions

### 1. Configuration-Driven
- All customization in JSON config
- No hard-coded values
- Easy to version control
- Easy to share between environments

### 2. Auto-Detection with Overrides
- Detects as much as possible
- User can override anything
- Sensible defaults for everything

### 3. Generic Functions
- `combine_fields_universal()` - works with any schema
- `chunk_text()` - generic chunking
- `create_embeddings_table()` - generic table creation

### 4. Interactive + Non-Interactive
- Wizard for first-time setup
- Config file for repeat runs
- Can run fully automated

---

## 🚀 Usage Examples

### Example 1: First Time Setup
```bash
# Run wizard
python scripts/setup/setup_embeddings.py

# Review generated config
cat config/embedding_config.json

# Edit if needed
nano config/embedding_config.json

# Generate embeddings
python scripts/core/generate_embeddings_universal.py
```

### Example 2: Using Existing Config
```bash
# Just run generation (uses existing config)
python scripts/core/generate_embeddings_universal.py
```

### Example 3: Different Model
```bash
# Edit config to use different model
# Change: "model": "sentence-transformers/all-mpnet-base-v2"
# Change: "dimension": 768

python scripts/core/generate_embeddings_universal.py
```

---

## ✅ Summary

**What Stays the Same:**
- Core functions (chunking, embedding generation)
- Database operations (table creation, batch inserts)
- Pipeline flow

**What Needs Input:**
- Database connection (required)
- Source table name (required)
- Primary key (auto-detected, can override)

**What Can Be Auto-Generated:**
- Schema detection
- Text field detection
- Default configuration
- Index tuning

**What User Can Customize:**
- Field selection and weights
- Field labels
- Chunking parameters
- Model choice
- Table names

This approach makes the script reusable for any client while allowing full customization when needed.

