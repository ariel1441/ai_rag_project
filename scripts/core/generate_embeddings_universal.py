"""
Universal embedding generation script.

Works with any table structure using configuration file.
DO NOT modify scripts/core/generate_embeddings.py (project-specific).
"""
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
import logging
from tqdm import tqdm
import json
import os
import sys
from pathlib import Path
from psycopg2.extras import execute_values

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.utils.text_processing_universal import combine_text_fields_universal, chunk_text

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/embedding_config.json") -> dict:
    """
    Load configuration file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dict
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        print(f"❌ ERROR: Configuration file not found: {config_file}")
        print()
        print("Please run the setup wizard first:")
        print("  python scripts/setup/setup_embeddings.py")
        return None
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Replace password placeholder with actual password
    if config['database']['password'] == "${POSTGRES_PASSWORD}":
        password = os.getenv("POSTGRES_PASSWORD")
        if not password:
            print("❌ ERROR: POSTGRES_PASSWORD not found in .env file!")
            return None
        config['database']['password'] = password
    
    return config


def create_embeddings_table(cursor, table_name: str, dimension: int, source_table: str, primary_key: str):
    """
    Create embeddings table with vector column.
    
    Args:
        cursor: Database cursor
        table_name: Name of embeddings table
        dimension: Vector dimension
        source_table: Source table name (for reference)
        primary_key: Primary key column name
    """
    # Drop if exists
    cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
    
    # Create table
    cursor.execute(f"""
        CREATE TABLE {table_name} (
            id SERIAL PRIMARY KEY,
            {primary_key} INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            text_chunk TEXT NOT NULL,
            embedding vector({dimension}) NOT NULL,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE({primary_key}, chunk_index)
        );
    """)
    
    # Create index for fast similarity search
    cursor.execute(f"""
        CREATE INDEX idx_{table_name}_vector 
        ON {table_name} 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)
    
    # Create index on primary key for joins
    cursor.execute(f"""
        CREATE INDEX idx_{table_name}_{primary_key} 
        ON {table_name} ({primary_key});
    """)


def load_source_data(cursor, config: dict) -> tuple:
    """
    Load data from source table.
    
    Returns:
        Tuple of (rows as dicts, column names)
    """
    source = config['source']
    table_name = source['table_name']
    limit = source.get('limit')
    
    query = f"SELECT * FROM {table_name}"
    if limit:
        query += f" LIMIT {limit}"
    query += f" ORDER BY {source['primary_key']};"
    
    cursor.execute(query)
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    # Convert to dicts
    data = [dict(zip(columns, row)) for row in rows]
    
    return data, columns


def main():
    """Main function."""
    print("=" * 80)
    print("UNIVERSAL EMBEDDING GENERATION")
    print("=" * 80)
    print()
    
    # Load config
    print("Step 1: Loading configuration...")
    config = load_config()
    if not config:
        return 1
    
    print(f"✓ Configuration loaded from: config/embedding_config.json")
    print(f"  Source table: {config['source']['table_name']}")
    print(f"  Primary key: {config['source']['primary_key']}")
    print(f"  Embeddings table: {config['output']['table_name']}")
    print()
    
    # Connect to database
    print("Step 2: Connecting to database...")
    db_config = config['database']
    
    try:
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password']
        )
        cursor = conn.cursor()
        print("✓ Database connection successful!")
        print()
    except Exception as e:
        print(f"❌ ERROR: Cannot connect to database: {e}")
        return 1
    
    try:
        # Check if embeddings table exists
        output_table = config['output']['table_name']
        cursor.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = '{output_table}'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            cursor.execute(f"SELECT COUNT(*) FROM {output_table};")
            existing_count = cursor.fetchone()[0]
            print(f"⚠️  WARNING: Embeddings table '{output_table}' already exists!")
            print(f"    Current embeddings: {existing_count:,}")
            print()
            
            response = input("Do you want to replace existing embeddings? (yes/no): ").strip().lower()
            if response not in ['yes', 'y']:
                print("Cancelled.")
                return 0
            print()
        
        # Load model
        print("Step 3: Loading embedding model...")
        print(f"  Model: {config['embedding']['model']}")
        print("  This may take 30-60 seconds on first run...")
        
        model = SentenceTransformer(config['embedding']['model'])
        dimension = config['embedding']['dimension']
        
        print("✓ Model loaded successfully!")
        print()
        
        # Load source data
        print("Step 4: Loading source data...")
        data, columns = load_source_data(cursor, config)
        
        if not data:
            print("❌ ERROR: No data found in source table!")
            return 1
        
        print(f"✓ Loaded {len(data):,} rows from '{config['source']['table_name']}'")
        print()
        
        # Create embeddings table
        print("Step 5: Creating embeddings table...")
        create_embeddings_table(
            cursor,
            output_table,
            dimension,
            config['source']['table_name'],
            config['source']['primary_key']
        )
        conn.commit()
        print(f"✓ Created table '{output_table}'")
        print()
        
        # Prepare documents
        print("Step 6: Preparing text documents...")
        print("  Combining fields and chunking text...")
        print()
        
        documents = []
        chunking_config = config['chunking']
        
        for row in tqdm(data, desc="Preparing documents"):
            primary_key_value = row.get(config['source']['primary_key'])
            if not primary_key_value:
                continue
            
            # Combine text fields using universal function
            combined_text = combine_text_fields_universal(row, config)
            
            if not combined_text:
                continue
            
            # Chunk text
            chunks = chunk_text(
                combined_text,
                max_chunk_size=chunking_config['max_chunk_size'],
                overlap=chunking_config['overlap']
            )
            
            for chunk_idx, chunk in enumerate(chunks):
                documents.append({
                    'primary_key': primary_key_value,
                    'chunk_index': chunk_idx,
                    'text_chunk': chunk,
                    'metadata': {
                        'source_table': config['source']['table_name']
                    }
                })
        
        print(f"✓ Created {len(documents):,} document chunks")
        print()
        
        if not documents:
            print("❌ ERROR: No documents created! Check field configuration.")
            return 1
        
        # Generate embeddings
        print("Step 7: Generating embeddings...")
        print(f"  Generating {len(documents):,} embeddings...")
        print("  This is the longest step - estimated time: 30-60 minutes per 8K rows")
        print("  You can leave this running and check back later.")
        print()
        
        texts = [doc['text_chunk'] for doc in documents]
        embedding_config = config['embedding']
        
        embeddings = model.encode(
            texts,
            batch_size=embedding_config['batch_size'],
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=embedding_config.get('normalize', True)
        )
        
        print()
        print(f"✓ Generated {len(embeddings):,} embeddings successfully!")
        print()
        
        # Insert into database
        print("Step 8: Inserting embeddings into database...")
        print(f"  Inserting {len(embeddings):,} embeddings in batches...")
        print()
        
        primary_key_col = config['source']['primary_key']
        records = []
        
        for i, doc in enumerate(documents):
            embedding_str = '[' + ','.join(map(str, embeddings[i])) + ']'
            records.append((
                doc['primary_key'],
                doc['chunk_index'],
                doc['text_chunk'],
                embedding_str,
                json.dumps(doc['metadata'])
            ))
        
        insert_query = f"""
            INSERT INTO {output_table} 
            ({primary_key_col}, chunk_index, text_chunk, embedding, metadata)
            VALUES %s
        """
        
        batch_size = 100
        for i in tqdm(range(0, len(records), batch_size), desc="Inserting batches"):
            batch = records[i:i+batch_size]
            execute_values(cursor, insert_query, batch)
            conn.commit()
        
        print()
        print(f"✓ Inserted {len(records):,} embeddings")
        print()
        
        # Verify
        print("Step 9: Verifying embeddings...")
        cursor.execute(f"SELECT COUNT(*) FROM {output_table};")
        count = cursor.fetchone()[0]
        
        print()
        print("=" * 80)
        print("✅ SUCCESS! Embedding generation complete!")
        print("=" * 80)
        print(f"Total embeddings stored: {count:,}")
        print(f"Total source rows processed: {len(data):,}")
        print(f"Embeddings table: {output_table}")
        print()
        print("Next steps:")
        print("  1. Test search functionality")
        print("  2. Use embeddings for semantic search")
        print()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        cursor.close()
        conn.close()
    
    return 0


if __name__ == "__main__":
    exit(main())

