"""
Create request_embeddings table for Docker PostgreSQL.
"""
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

try:
    conn = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', 5433)),
        database=os.getenv('POSTGRES_DATABASE', 'ai_requests_db'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'password'),
    )
    
    # Register pgvector
    from pgvector.psycopg2 import register_vector
    register_vector(conn)
    
    cursor = conn.cursor()
    
    print("Creating request_embeddings table...")
    
    # Create table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS request_embeddings (
            id SERIAL PRIMARY KEY,
            requestid VARCHAR(100) NOT NULL,
            chunk_index INTEGER NOT NULL DEFAULT 0,
            text_chunk TEXT NOT NULL,
            embedding vector(384) NOT NULL,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(requestid, chunk_index)
        );
    """)
    
    # Create vector index
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_request_embeddings_vector 
        ON request_embeddings 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """)
    
    # Create index on requestid
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_request_embeddings_requestid 
        ON request_embeddings(requestid);
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("✅ request_embeddings table created successfully!")
    print("   - Table: request_embeddings")
    print("   - Vector dimension: 384")
    print("   - Indexes created")
    
except Exception as e:
    print(f"❌ Error: {e}")

