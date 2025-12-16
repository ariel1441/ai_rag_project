"""
Interactive setup wizard for embedding generation.

This creates a configuration file that can be used by the universal embedding generator.
"""
import os
import json
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.setup.auto_detect_schema import detect_schema, get_database_connection, detect_table_schema
from scripts.setup.intelligent_field_analysis import analyze_table_fields


def print_header(title: str):
    """Print a formatted header."""
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)
    print()


def get_database_connection_interactive():
    """Get database connection interactively or from .env."""
    print_header("DATABASE CONNECTION")
    
    # Try .env first
    from dotenv import load_dotenv
    load_dotenv()
    
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    database = os.getenv("POSTGRES_DATABASE")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    
    if host and database and user and password:
        print("✓ Found database configuration in .env file")
        print(f"  Host: {host}:{port or '5433'}")
        print(f"  Database: {database}")
        print(f"  User: {user}")
        print()
        
        use_env = input("Use this configuration? (yes/no) [yes]: ").strip().lower()
        if use_env != 'no':
            return {
                'host': host,
                'port': int(port) if port else 5433,
                'database': database,
                'user': user,
                'password': password
            }
    
    # Interactive input
    print("Enter database connection details:")
    host = input("Host [localhost]: ").strip() or "localhost"
    port = input("Port [5433]: ").strip() or "5433"
    database = input("Database: ").strip()
    user = input("User [postgres]: ").strip() or "postgres"
    password = input("Password: ").strip()
    
    if not database or not password:
        print("❌ Error: Database and password are required!")
        return None
    
    return {
        'host': host,
        'port': int(port),
        'database': database,
        'user': user,
        'password': password
    }


def import_csv_option(connection_params: dict):
    """Option to import CSV file first."""
    print_header("CSV IMPORT OPTION")
    
    print("Do you want to import a CSV file first?")
    print("(Useful if your data is in SQL Server, MySQL, or another database)")
    print()
    
    choice = input("Import CSV file? (yes/no) [no]: ").strip().lower()
    
    if choice not in ['yes', 'y']:
        return None
    
    csv_path = input("Enter CSV file path: ").strip()
    
    if not csv_path or not Path(csv_path).exists():
        print(f"❌ CSV file not found: {csv_path}")
        return None
    
    table_name = input("Enter table name for imported data: ").strip()
    
    if not table_name:
        print("❌ Table name is required!")
        return None
    
    print()
    print("Importing CSV to PostgreSQL...")
    
    from scripts.helpers.import_csv_to_postgres import import_csv_to_postgres
    
    result = import_csv_to_postgres(csv_path, table_name, connection_params)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return None
    
    print()
    print("=" * 80)
    print("✅ CSV IMPORT COMPLETE!")
    print("=" * 80)
    print(f"Table: {result['table_name']}")
    print(f"Rows imported: {result['rows_imported']:,}")
    print()
    
    return result['table_name']


def select_table(connection_params: dict):
    """Let user select a table from the database or import CSV."""
    print_header("TABLE SELECTION")
    
    # Option 1: Import CSV
    imported_table = import_csv_option(connection_params)
    if imported_table:
        return imported_table
    
    # Option 2: Select existing table
    print("Detecting tables in database...")
    result = detect_schema(connection_params)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return None
    
    tables = result['tables']
    
    if not tables:
        print("❌ No tables found in database!")
        print()
        print("Options:")
        print("  1. Import CSV file (run setup wizard again)")
        print("  2. Create table manually in PostgreSQL")
        return None
    
    print(f"Found {len(tables)} tables:")
    print()
    
    for i, table in enumerate(tables, 1):
        schema = result['schemas'][table]
        print(f"{i}. {table}")
        print(f"   Rows: {schema['row_count']:,}")
        print(f"   Columns: {len(schema['columns'])}")
        print(f"   Primary Key (suggested): {schema['primary_key']}")
        print()
    
    print("Or enter 'csv' to import a CSV file")
    print()
    
    while True:
        try:
            choice = input(f"Select table (1-{len(tables)}) or enter table name: ").strip()
            
            if choice.lower() == 'csv':
                imported_table = import_csv_option(connection_params)
                if imported_table:
                    return imported_table
                continue
            
            # Try as number
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(tables):
                    return tables[idx]
                else:
                    print(f"❌ Invalid number. Please enter 1-{len(tables)}")
            # Try as table name
            elif choice in tables:
                return choice
            else:
                print(f"❌ Table '{choice}' not found. Please try again.")
        except KeyboardInterrupt:
            print("\nCancelled.")
            return None


def confirm_primary_key(schema: dict):
    """Confirm or change primary key suggestion."""
    print_header("PRIMARY KEY")
    
    suggested = schema['primary_key']
    print(f"Suggested primary key: {suggested}")
    print()
    
    # Show all columns
    print("Available columns:")
    for i, col in enumerate(schema['columns'][:20], 1):  # Show first 20
        marker = " ← suggested" if col['name'] == suggested else ""
        print(f"  {col['name']} ({col['type']}){marker}")
    if len(schema['columns']) > 20:
        print(f"  ... and {len(schema['columns']) - 20} more")
    print()
    
    choice = input(f"Use '{suggested}' as primary key? (yes/no) [yes]: ").strip().lower()
    
    if choice == 'no':
        new_key = input("Enter primary key column name: ").strip()
        if new_key in [col['name'] for col in schema['columns']]:
            return new_key
        else:
            print(f"⚠️  '{new_key}' not found in columns. Using suggested '{suggested}'")
            return suggested
    
    return suggested


def run_intelligent_analysis(cursor, table_name: str):
    """Run intelligent field analysis and get weight suggestions."""
    print_header("INTELLIGENT FIELD ANALYSIS")
    
    print("Analyzing table structure and data...")
    print("This may take a minute...")
    print()
    
    result = analyze_table_fields(cursor, table_name, sample_size=1000)
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
        return None
    
    weights = result['weights']
    analysis = result['analysis']
    
    print(f"✓ Analysis complete!")
    print()
    print(f"Field Weight Suggestions:")
    print(f"  🔴 3.0x (Critical): {len(weights['3.0x'])} fields")
    print(f"  🟠 2.0x (Important): {len(weights['2.0x'])} fields")
    print(f"  🟡 1.0x (Supporting): {len(weights['1.0x'])} fields")
    print(f"  ⚪ 0.5x (Low): {len(weights.get('0.5x', []))} fields")
    print(f"  ❌ Excluded: {len(weights['exclude'])} fields")
    print()
    
    # Show top fields
    print("Top Critical Fields (3.0x):")
    for field in weights['3.0x'][:10]:
        field_analysis = next((r for r in analysis['results'] if r['column'] == field), None)
        if field_analysis:
            coverage = field_analysis.get('data_analysis', {}).get('coverage', 0) * 100
            print(f"  - {field} (Coverage: {coverage:.1f}%)")
    if len(weights['3.0x']) > 10:
        print(f"  ... and {len(weights['3.0x']) - 10} more")
    print()
    
    return weights


def generate_config(connection_params: dict, table_name: str, primary_key: str, 
                   weights: dict, schema: dict, chunking: dict, embedding: dict):
    """Generate configuration file."""
    config = {
        "database": {
            "host": connection_params['host'],
            "port": connection_params['port'],
            "database": connection_params['database'],
            "user": connection_params['user'],
            "password": "${POSTGRES_PASSWORD}"  # Use env variable
        },
        "source": {
            "table_name": table_name,
            "primary_key": primary_key,
            "limit": None
        },
        "fields": {
            "include_all": True,
            "exclude": weights.get('exclude', []),
            "weights": {
                "3.0x": weights.get('3.0x', []),
                "2.0x": weights.get('2.0x', []),
                "1.0x": weights.get('1.0x', [])
            },
            "labels": {
                col['name']: col['name'].replace('_', ' ').title()
                for col in schema['columns']
            }
        },
        "chunking": chunking,
        "embedding": embedding,
        "output": {
            "table_name": f"{table_name}_embeddings",
            "create_index": True,
            "index_lists": None  # Auto-calculate
        }
    }
    
    return config


def main():
    """Main setup wizard."""
    print_header("EMBEDDING SETUP WIZARD")
    print("This wizard will help you set up embedding generation for any table.")
    print()
    
    # Step 1: Database connection
    connection_params = get_database_connection_interactive()
    if not connection_params:
        print("❌ Setup cancelled.")
        return 1
    
    # Step 2: Connect and select table
    conn = get_database_connection()
    if not conn:
        # Try with provided params
        import psycopg2
        try:
            conn = psycopg2.connect(**connection_params)
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            return 1
    
    cursor = conn.cursor()
    
    try:
        # Step 3: Select table
        table_name = select_table(connection_params)
        if not table_name:
            print("❌ Setup cancelled.")
            return 1
        
        # Get schema for selected table
        schema = detect_table_schema(cursor, table_name)
        
        # Step 4: Confirm primary key
        primary_key = confirm_primary_key(schema)
        
        # Step 5: Run intelligent analysis
        weights = run_intelligent_analysis(cursor, table_name)
        if not weights:
            print("⚠️  Could not run intelligent analysis. Using defaults.")
            weights = {
                '3.0x': schema['text_fields'][:5] if len(schema['text_fields']) >= 5 else schema['text_fields'],
                '2.0x': schema['text_fields'][5:10] if len(schema['text_fields']) >= 10 else [],
                '1.0x': schema['text_fields'][10:] if len(schema['text_fields']) > 10 else [],
                'exclude': []
            }
        
        # Step 6: Chunking parameters
        print_header("CHUNKING PARAMETERS")
        chunk_size = input("Chunk size [512]: ").strip() or "512"
        overlap = input("Overlap [50]: ").strip() or "50"
        chunking = {
            "max_chunk_size": int(chunk_size),
            "overlap": int(overlap)
        }
        
        # Step 7: Embedding model
        print_header("EMBEDDING MODEL")
        print("Available models:")
        print("  1. all-MiniLM-L6-v2 (384 dims, fast, recommended)")
        print("  2. all-mpnet-base-v2 (768 dims, slower, better quality)")
        print("  3. Custom (enter model name)")
        print()
        
        model_choice = input("Select model [1]: ").strip() or "1"
        
        if model_choice == "1":
            model = "sentence-transformers/all-MiniLM-L6-v2"
            dimension = 384
        elif model_choice == "2":
            model = "sentence-transformers/all-mpnet-base-v2"
            dimension = 768
        else:
            model = input("Enter model name: ").strip()
            dimension_input = input("Enter dimension: ").strip()
            dimension = int(dimension_input) if dimension_input.isdigit() else 384
        
        embedding = {
            "model": model,
            "dimension": dimension,
            "batch_size": 32,
            "normalize": True
        }
        
        # Step 8: Generate config
        print_header("GENERATING CONFIGURATION")
        
        config = generate_config(
            connection_params,
            table_name,
            primary_key,
            weights,
            schema,
            chunking,
            embedding
        )
        
        # Step 9: Save config
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "embedding_config.json"
        
        print(f"Saving configuration to: {config_file}")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print()
        print("=" * 80)
        print("✅ SETUP COMPLETE!")
        print("=" * 80)
        print()
        print(f"Configuration saved to: {config_file}")
        print()
        print("Next steps:")
        print("  1. Review the configuration file if needed")
        print("  2. Run: python scripts/core/generate_embeddings_universal.py")
        print()
        
    finally:
        cursor.close()
        conn.close()
    
    return 0


if __name__ == "__main__":
    exit(main())

