"""
Auto-detect database schema for embedding setup.

Detects:
- All tables in database
- Columns and types for each table
- Primary key suggestions
- Text field suggestions
"""
import psycopg2
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv


def get_database_connection():
    """Get database connection from .env or return None."""
    load_dotenv()
    
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5433"))
    database = os.getenv("POSTGRES_DATABASE")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")
    
    if not database or not password:
        return None
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


def detect_all_tables(cursor) -> List[str]:
    """
    Detect all tables in the database.
    
    Returns:
        List of table names
    """
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    
    tables = [row[0] for row in cursor.fetchall()]
    return tables


def detect_table_schema(cursor, table_name: str) -> Dict:
    """
    Detect schema for a specific table.
    
    Returns:
        Dict with columns, primary_key suggestion, text_fields suggestion
    """
    # Get columns
    cursor.execute("""
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_name = %s
        AND table_schema = 'public'
        ORDER BY ordinal_position;
    """, (table_name,))
    
    columns = []
    for row in cursor.fetchall():
        columns.append({
            'name': row[0],
            'type': row[1],
            'nullable': row[2] == 'YES',
            'default': row[3]
        })
    
    # Detect primary key
    primary_key = suggest_primary_key(columns, table_name)
    
    # Detect text fields
    text_fields = suggest_text_fields(columns)
    
    # Get row count
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        row_count = cursor.fetchone()[0]
    except:
        row_count = 0
    
    return {
        'table_name': table_name,
        'columns': columns,
        'primary_key': primary_key,
        'text_fields': text_fields,
        'row_count': row_count
    }


def suggest_primary_key(columns: List[Dict], table_name: str) -> Optional[str]:
    """
    Suggest primary key column.
    
    Common patterns:
    - {table}_id
    - id
    - {table}id
    - Primary key constraint
    """
    table_name_lower = table_name.lower()
    
    # Check for explicit primary key constraint
    # (This would require checking constraints, but for now we use patterns)
    
    # Pattern 1: {table}_id
    pattern1 = f"{table_name_lower}_id"
    for col in columns:
        if col['name'].lower() == pattern1:
            return col['name']
    
    # Pattern 2: id
    for col in columns:
        if col['name'].lower() == 'id':
            return col['name']
    
    # Pattern 3: {table}id
    pattern3 = f"{table_name_lower}id"
    for col in columns:
        if col['name'].lower() == pattern3:
            return col['name']
    
    # Pattern 4: ends with _id
    for col in columns:
        if col['name'].lower().endswith('_id'):
            return col['name']
    
    # Pattern 5: ends with id (but not _id)
    for col in columns:
        name_lower = col['name'].lower()
        if name_lower.endswith('id') and not name_lower.endswith('_id'):
            return col['name']
    
    # Fallback: first column
    if columns:
        return columns[0]['name']
    
    return None


def suggest_text_fields(columns: List[Dict]) -> List[str]:
    """
    Suggest which fields are likely text fields for embeddings.
    
    Excludes:
    - IDs (ends with _id, id)
    - Dates (date, timestamp)
    - Booleans (boolean)
    - Numbers (integer, numeric)
    - System fields (created_at, updated_at)
    """
    text_fields = []
    exclude_patterns = ['_id', '_uuid', '_guid', 'created_at', 'updated_at', 'deleted_at']
    
    for col in columns:
        name_lower = col['name'].lower()
        type_lower = col['type'].lower()
        
        # Skip if matches exclude pattern
        if any(pattern in name_lower for pattern in exclude_patterns):
            continue
        
        # Skip if ends with 'id' (likely foreign key)
        if name_lower.endswith('id') and name_lower != 'id':
            continue
        
        # Include text-like types
        if 'text' in type_lower or 'varchar' in type_lower or 'char' in type_lower:
            text_fields.append(col['name'])
        # Include if name suggests text content
        elif any(word in name_lower for word in ['name', 'desc', 'description', 'title', 'content', 'text', 'remark', 'note', 'comment', 'message']):
            text_fields.append(col['name'])
    
    return text_fields


def detect_schema(connection_params: Dict = None) -> Dict:
    """
    Main function to detect database schema.
    
    Args:
        connection_params: Optional dict with host, port, database, user, password
                          If None, uses .env file
    
    Returns:
        Dict with tables and their schemas
    """
    if connection_params:
        conn = psycopg2.connect(**connection_params)
    else:
        conn = get_database_connection()
    
    if not conn:
        return {'error': 'Could not connect to database'}
    
    cursor = conn.cursor()
    
    try:
        # Detect all tables
        tables = detect_all_tables(cursor)
        
        if not tables:
            return {'error': 'No tables found in database'}
        
        # Detect schema for each table
        schemas = {}
        for table in tables:
            schemas[table] = detect_table_schema(cursor, table)
        
        return {
            'tables': tables,
            'schemas': schemas
        }
    
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Test the schema detection
    print("=" * 80)
    print("AUTO-DETECT DATABASE SCHEMA")
    print("=" * 80)
    print()
    
    result = detect_schema()
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"Found {len(result['tables'])} tables:")
        print()
        
        for table_name in result['tables'][:10]:  # Show first 10
            schema = result['schemas'][table_name]
            print(f"Table: {table_name}")
            print(f"  Rows: {schema['row_count']:,}")
            print(f"  Columns: {len(schema['columns'])}")
            print(f"  Primary Key (suggested): {schema['primary_key']}")
            print(f"  Text Fields (suggested): {len(schema['text_fields'])} fields")
            if schema['text_fields']:
                print(f"    {', '.join(schema['text_fields'][:5])}")
                if len(schema['text_fields']) > 5:
                    print(f"    ... and {len(schema['text_fields']) - 5} more")
            print()

