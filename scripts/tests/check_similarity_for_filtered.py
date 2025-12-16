"""Check similarity scores for requests that should match."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from dotenv import load_dotenv

load_dotenv()

def check_similarity():
    """Check similarity scores."""
    search_service = SearchService()
    search_service.connect_db()
    
    query = "פניות מיניב ליבוביץ בסטטוס 1"
    
    # Generate embedding
    model = search_service._get_embedding_model()
    query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
    
    # Insert into temp table
    search_service.cursor.execute("DROP TABLE IF EXISTS temp_query_embedding;")
    search_service.cursor.execute("CREATE TEMP TABLE temp_query_embedding (embedding vector(384));")
    search_service.cursor.execute("INSERT INTO temp_query_embedding (embedding) VALUES (%s);", (query_embedding.tolist(),))
    
    # Check similarity for requests that match both filters
    search_service.cursor.execute("""
        SELECT 
            e.requestid,
            1 - (e.embedding <=> t.embedding) as similarity,
            r.requeststatusid
        FROM request_embeddings e
        INNER JOIN requests r ON e.requestid = r.requestid
        CROSS JOIN temp_query_embedding t
        WHERE r.requeststatusid::TEXT = '1'::TEXT
        AND e.text_chunk LIKE '%יניב ליבוביץ%'
        AND e.embedding IS NOT NULL
        ORDER BY similarity DESC
        LIMIT 10
    """)
    
    results = search_service.cursor.fetchall()
    print(f"Similarity scores for requests matching both filters:")
    print(f"Threshold: 0.4 (general intent)")
    print()
    
    for req_id, similarity, status_id in results:
        status = "✅" if similarity >= 0.4 else "❌"
        print(f"{status} RequestID: {req_id}, Status: {status_id}, Similarity: {similarity:.4f}")
    
    search_service.close()

if __name__ == "__main__":
    check_similarity()

