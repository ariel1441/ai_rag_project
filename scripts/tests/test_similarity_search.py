"""
Test similarity search - find similar requests.
"""
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
import os
import sys

# Fix encoding
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    except:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def main():
    print("=" * 70)
    print("Similarity Search Test")
    print("=" * 70)
    print()
    print("This script will:")
    print("  1. Ask you for a search query")
    print("  2. Generate an embedding for your query")
    print("  3. Search for similar requests in the database")
    print("  4. Show you the results with similarity scores")
    print()
    
    # Connection details (from .env, no prompts)
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")
    database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")
    
    if not password:
        print("ERROR: POSTGRES_PASSWORD not found in .env file!")
        print("Create .env file with your password (see env.example.txt)")
        return 1
    
    # Get query
    query = input("Enter search query (e.g., 'אלינור', 'בדיקה'): ").strip()
    if not query:
        print("No query provided. Exiting.")
        return
    
    print()
    print("=" * 70)
    print("Processing...")
    print("=" * 70)
    print()
    
    try:
        # Connect to database
        print("Connecting to database...")
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        print("✓ Connected")
        print()
        
        # Convert query to embedding
        print("Generating embedding for query...")
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
        print(f"✓ Embedding generated: {len(query_embedding)} dimensions")
        print()
        
        # Format embedding for PostgreSQL
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        # Search
        print("Searching database...")
        search_query = f"""
            SELECT 
                requestid,
                chunk_index,
                text_chunk,
                1 - (embedding <=> '{embedding_str}'::vector) as similarity
            FROM request_embeddings
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> '{embedding_str}'::vector
            LIMIT 10;
        """
        
        cursor.execute(search_query)
        results = cursor.fetchall()
        
        print(f"✓ Found {len(results)} results")
        print()
        
        if results:
            print("=" * 70)
            print("RESULTS")
            print("=" * 70)
            print()
            
            for i, (req_id, chunk_idx, text_chunk, similarity) in enumerate(results, 1):
                similarity_pct = similarity * 100
                print(f"{i}. Request {req_id} (Chunk {chunk_idx})")
                print(f"   Similarity: {similarity:.4f} ({similarity_pct:.2f}%)")
                print(f"   Text: {text_chunk[:200]}")
                print()
        else:
            print("⚠ No results found")
            print()
            print("Debugging:")
            cursor.execute("SELECT COUNT(*) FROM request_embeddings;")
            total = cursor.fetchone()[0]
            print(f"  Total embeddings: {total}")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    main()

