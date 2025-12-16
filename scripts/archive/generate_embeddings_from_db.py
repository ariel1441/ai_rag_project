"""
Generate embeddings from requests table in PostgreSQL and store in request_embeddings.
This reads directly from the database instead of a file.
"""
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
import logging
from tqdm import tqdm
import json
import os
from pathlib import Path
from psycopg2.extras import execute_values

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def combine_text_fields(request):
    """Combine relevant text fields from a request."""
    fields = []
    
    if request.get('projectname'):
        fields.append(f"Project: {request['projectname']}")
    if request.get('projectdesc'):
        fields.append(f"Description: {request['projectdesc']}")
    if request.get('areadesc'):
        fields.append(f"Area: {request['areadesc']}")
    if request.get('remarks'):
        fields.append(f"Remarks: {request['remarks']}")
    if request.get('requestjobshortdescription'):
        fields.append(f"Job: {request['requestjobshortdescription']}")
    if request.get('requeststatusid'):
        fields.append(f"Status ID: {request['requeststatusid']}")
    if request.get('requesttypeid'):
        fields.append(f"Type ID: {request['requesttypeid']}")
    
    return " | ".join(fields) if fields else ""

def chunk_text(text, max_chunk_size=512, overlap=50):
    """Split text into chunks with overlap."""
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for period or pipe separator
            for sep in ['. ', ' | ']:
                last_sep = text.rfind(sep, start, end)
                if last_sep != -1:
                    end = last_sep + len(sep)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks if chunks else [text]

def main():
    print("=" * 70)
    print("Generate Embeddings from PostgreSQL")
    print("=" * 70)
    print()
    
    try:
        # Connection details (from .env, no prompts)
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5433")
        database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD")
        
        if not password:
            print("ERROR: POSTGRES_PASSWORD not found in .env file!")
            print("Please create .env file with your password.")
            print("See env.example.txt for format.")
            return 1
        
        print(f"Using connection: {host}:{port}/{database} as {user}")
        print()
        
        # Connect
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        
        # Load model
        print("Loading embedding model...")
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        print("✓ Model loaded")
        print()
        
        # Load requests
        print("Loading requests from database...")
        cursor.execute("""
            SELECT * FROM requests
            ORDER BY requestid;
        """)
        
        columns = [desc[0] for desc in cursor.description]
        requests = [dict(zip(columns, row)) for row in cursor.fetchall()]
        logger.info(f"Loaded {len(requests)} requests")
        
        # Prepare documents (combine text and chunk if needed)
        print()
        print("Preparing text documents...")
        documents = []
        
        for req in tqdm(requests, desc="Preparing documents"):
            request_id = str(req['requestid']) if req['requestid'] else None
            if not request_id:
                continue
            
            # Combine text fields
            combined_text = combine_text_fields(req)
            
            # Chunk if necessary
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
        
        # Generate embeddings
        print()
        print("Generating embeddings...")
        texts = [doc['text_chunk'] for doc in documents]
        embeddings = model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        logger.info(f"Generated {len(embeddings)} embeddings")
        
        # Insert into database
        print()
        print("Inserting embeddings into database...")
        
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
        cursor.execute("SELECT COUNT(*) FROM request_embeddings;")
        count = cursor.fetchone()[0]
        
        print()
        print("=" * 70)
        print("SUCCESS!")
        print("=" * 70)
        print(f"Total embeddings stored: {count}")
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

