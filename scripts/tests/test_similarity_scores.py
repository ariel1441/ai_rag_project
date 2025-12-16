"""Check similarity scores for queries to see if threshold is too strict."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from dotenv import load_dotenv

load_dotenv()

def check_similarity_scores():
    """Check similarity scores for queries."""
    print("=" * 80)
    print("CHECKING SIMILARITY SCORES")
    print("=" * 80)
    print()
    
    search_service = SearchService()
    search_service.connect_db()
    
    # Generate embedding for query
    query = "פניות מיניב ליבוביץ"
    model = search_service._get_embedding_model()
    query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
    
    # Insert into temp table
    search_service.cursor.execute("DROP TABLE IF EXISTS temp_query_embedding;")
    search_service.cursor.execute("CREATE TEMP TABLE temp_query_embedding (embedding vector(384));")
    search_service.cursor.execute("INSERT INTO temp_query_embedding (embedding) VALUES (%s);", (query_embedding.tolist(),))
    
    # Check similarity scores without threshold
    search_service.cursor.execute("""
        SELECT 
            e.requestid,
            1 - (e.embedding <=> t.embedding) as similarity
        FROM request_embeddings e
        CROSS JOIN temp_query_embedding t
        WHERE e.embedding IS NOT NULL
        ORDER BY similarity DESC
        LIMIT 30
    """)
    
    results = search_service.cursor.fetchall()
    print(f"Top 30 similarity scores for: {query}")
    print(f"Threshold: 0.5 (for person queries)")
    print()
    
    above_threshold = 0
    for req_id, similarity in results:
        status = "✅" if similarity >= 0.5 else "❌"
        if similarity >= 0.5:
            above_threshold += 1
        print(f"{status} RequestID: {req_id}, Similarity: {similarity:.4f}")
    
    print()
    print(f"Results above threshold (0.5): {above_threshold}/30")
    print(f"Results below threshold: {30 - above_threshold}/30")
    
    if above_threshold == 0:
        print("\n⚠️  Threshold might be too strict - no results pass!")
        print("   Consider lowering threshold for person queries")
    
    search_service.close()

if __name__ == "__main__":
    check_similarity_scores()

