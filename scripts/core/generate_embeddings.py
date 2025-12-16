"""
Generate embeddings from requests table in PostgreSQL and store in request_embeddings.
This reads directly from the database instead of a file.

Uses the improved weighted field combination with ~44 fields.
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

# Add scripts directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.text_processing import combine_text_fields_weighted, chunk_text

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    print("=" * 70)
    print("Generate Embeddings from PostgreSQL")
    print("=" * 70)
    print()
    print("⚠️  IMPORTANT: This will REPLACE all existing embeddings!")
    print("    Make sure you have a backup if needed.")
    print()
    print("💡 TIP: Run 'python scripts/helpers/backup_embeddings_table.py' first to backup!")
    print()
    
    # Ask user if they want to continue
    response = input("Do you want to continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Cancelled.")
        return
    print()
    
    try:
        # Connection details (from .env, no prompts)
        print("Step 1: Loading configuration...")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5433")
        database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD")
        
        if not password:
            print("❌ ERROR: POSTGRES_PASSWORD not found in .env file!")
            print("Please create .env file with your password.")
            print("See env.example.txt for format.")
            return 1
        
        print(f"✓ Configuration loaded")
        print(f"  Host: {host}:{port}")
        print(f"  Database: {database}")
        print(f"  User: {user}")
        print()
        
        # Connect
        print("Step 2: Connecting to database...")
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        print("✓ Database connection successful!")
        print()
        
        # Check current embeddings count and offer backup
        print("Step 3: Checking current state...")
        cursor.execute("SELECT COUNT(*) FROM request_embeddings;")
        current_count = cursor.fetchone()[0]
        print(f"  Current embeddings in database: {current_count:,}")
        print()
        
        if current_count > 0:
            print("⚠️  WARNING: You have existing embeddings that will be DELETED!")
            print()
            print("💡 RECOMMENDED: Create a backup first!")
            print("   Run: python scripts/helpers/backup_embeddings_table.py")
            print()
            backup_response = input("Do you want to create a backup now? (yes/no): ").strip().lower()
            if backup_response in ['yes', 'y']:
                print()
                print("Creating backup...")
                try:
                    # Import and run backup function
                    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'helpers'))
                    from backup_embeddings_table import backup_embeddings_table
                    backup_table_name = backup_embeddings_table(silent=False)
                    if backup_table_name:
                        print()
                        print("✓ Backup complete! Continuing with regeneration...")
                        print()
                    else:
                        print("⚠️  Backup failed. Continuing anyway...")
                        print()
                except Exception as e:
                    print(f"⚠️  Backup failed: {e}")
                    print("   Continuing anyway (you can backup manually)...")
                    print()
            else:
                print("⚠️  No backup created. Continuing with regeneration...")
                print()
        
        # Load model
        print("Step 4: Loading embedding model...")
        print("  This may take 30-60 seconds on first run...")
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print("✓ Model loaded successfully!")
        print()
        
        # Load requests
        print("Step 5: Loading requests from database...")
        # First check what the ID column is called
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'requests'
            AND column_name IN ('requestid', 'request_id', 'id')
            ORDER BY CASE column_name 
                WHEN 'requestid' THEN 1 
                WHEN 'request_id' THEN 2 
                WHEN 'id' THEN 3 
            END
            LIMIT 1;
        """)
        id_col_result = cursor.fetchone()
        id_column = id_col_result[0] if id_col_result else 'requestid'
        
        cursor.execute(f"""
            SELECT * FROM requests
            ORDER BY "{id_column}";
        """)
        
        columns = [desc[0] for desc in cursor.description]
        requests = [dict(zip(columns, row)) for row in cursor.fetchall()]
        print(f"✓ Loaded {len(requests):,} requests from database")
        logger.info(f"Loaded {len(requests)} requests")
        print()
        
        if len(requests) == 0:
            print("❌ ERROR: No requests found in database!")
            print("Please import data first.")
            return 1
        
        # Clear old embeddings
        print("Step 6: Clearing old embeddings...")
        cursor.execute("TRUNCATE TABLE request_embeddings;")
        conn.commit()
        print("✓ Old embeddings cleared")
        print()
        
        # Prepare documents (combine text and chunk if needed)
        print("Step 7: Preparing text documents...")
        print("  This will combine all fields using the new weighted function...")
        print("  Estimated time: 1-2 minutes for 1,175 requests")
        print()
        documents = []
        
        for req in tqdm(requests, desc="Preparing documents"):
            request_id = str(req['requestid']) if req['requestid'] else None
            if not request_id:
                continue
            
            # Combine text fields using weighted version (includes ~44 fields)
            combined_text = combine_text_fields_weighted(req)
            
            # Chunk if necessary
            # Note: 512 is standard for embedding models (token/character limit)
            # With ~44 fields repeated 2-3 times, text can be 1000-5000 chars
            # So we'll have multiple chunks per request (that's OK!)
            chunks = chunk_text(combined_text, max_chunk_size=512, overlap=50)
            
            for chunk_idx, chunk in enumerate(chunks):
                documents.append({
                    'requestid': request_id,
                    'chunk_index': chunk_idx,
                    'text_chunk': chunk,
                    'metadata': {
                        'requeststatusid': str(req.get('requeststatusid', '')),
                        'requesttypeid': str(req.get('requesttypeid', ''))
                    }
                })
        
        logger.info(f"Created {len(documents)} document chunks")
        print(f"✓ Created {len(documents):,} document chunks")
        print()
        
        # Generate embeddings
        print("Step 8: Generating embeddings...")
        print(f"  Generating {len(documents):,} embeddings...")
        print("  This is the longest step - estimated time: 1-2 hours")
        print("  You can leave this running and check back later.")
        print()
        texts = [doc['text_chunk'] for doc in documents]
        embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        logger.info(f"Generated {len(embeddings)} embeddings")
        print()
        print(f"✓ Generated {len(embeddings):,} embeddings successfully!")
        print()
        
        # Insert into database
        print("Step 9: Inserting embeddings into database...")
        print(f"  Inserting {len(embeddings):,} embeddings in batches...")
        print()
        
        # Prepare records for insertion
        records = []
        for i, doc in enumerate(documents):
            embedding_str = '[' + ','.join(map(str, embeddings[i])) + ']'
            records.append((
                doc['requestid'],
                doc['chunk_index'],
                doc['text_chunk'],
                embedding_str,
                json.dumps(doc['metadata'])
            ))
        
        # Insert in batches
        insert_query = """
            INSERT INTO request_embeddings 
            (requestid, chunk_index, text_chunk, embedding, metadata)
            VALUES %s
        """
        
        batch_size = 100
        for i in tqdm(range(0, len(records), batch_size), desc="Inserting batches"):
            batch = records[i:i+batch_size]
            execute_values(cursor, insert_query, batch)
            conn.commit()
        
        logger.info(f"Inserted {len(records)} embeddings")
        
        # Verify
        print("Step 10: Verifying embeddings...")
        cursor.execute("SELECT COUNT(*) FROM request_embeddings;")
        count = cursor.fetchone()[0]
        
        print()
        print("=" * 70)
        print("✅ SUCCESS! Embedding generation complete!")
        print("=" * 70)
        print(f"Total embeddings stored: {count:,}")
        print(f"Total requests processed: {len(requests):,}")
        print()
        print("Next steps:")
        print("  1. Test search: python scripts/core/search.py")
        print("  2. Try query: 'פניות מאריאל בן עקיבא' (should now work!)")
        print()
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

