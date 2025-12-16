"""Debug why count query returns 0 when similarity scores are above threshold."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from dotenv import load_dotenv

load_dotenv()

def debug_count_query():
    """Debug the count query."""
    search_service = SearchService()
    search_service.connect_db()
    
    query = "פניות מיניב ליבוביץ"
    
    # Parse query
    parsed = search_service.query_parser.parse(query)
    entities = parsed.get('entities', {})
    intent = parsed.get('intent', 'general')
    
    print(f"Query: {query}")
    print(f"Intent: {intent}")
    print(f"Entities: {entities}")
    print()
    
    # Generate embedding
    model = search_service._get_embedding_model()
    query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
    
    # Insert into temp table
    search_service.cursor.execute("DROP TABLE IF EXISTS temp_query_embedding;")
    search_service.cursor.execute("CREATE TEMP TABLE temp_query_embedding (embedding vector(384));")
    search_service.cursor.execute("INSERT INTO temp_query_embedding (embedding) VALUES (%s);", (query_embedding.tolist(),))
    
    # Check what embedding_where would be
    embedding_where = "WHERE e.embedding IS NOT NULL"
    join_sql = ""
    
    # Check if has_multiple
    structured_entities = ['type_id', 'status_id', 'date_range', 'urgency']
    text_entities = ['person_name', 'project_name']
    has_structured = any(key in entities for key in structured_entities)
    has_text = any(key in entities for key in text_entities)
    has_multiple = (has_structured and has_text) or (len([k for k in text_entities if k in entities]) > 1)
    
    print(f"has_structured: {has_structured}")
    print(f"has_text: {has_text}")
    print(f"has_multiple: {has_multiple}")
    print()
    
    # Similarity threshold
    if intent in ['person', 'project']:
        similarity_threshold = 0.5
    else:
        similarity_threshold = 0.4
    
    print(f"Similarity threshold: {similarity_threshold}")
    print()
    
    # Test count query
    count_sql = f"""
        SELECT COUNT(DISTINCT e.requestid)
        FROM request_embeddings e
        {join_sql if join_sql else ""}
        CROSS JOIN temp_query_embedding t
        {embedding_where}
        AND (1 - (e.embedding <=> t.embedding)) >= {similarity_threshold}
    """
    
    print("Count SQL:")
    print(count_sql)
    print()
    
    search_service.cursor.execute(count_sql)
    count = search_service.cursor.fetchone()[0]
    print(f"Count result: {count}")
    
    # Test without threshold
    count_sql_no_threshold = f"""
        SELECT COUNT(DISTINCT e.requestid)
        FROM request_embeddings e
        CROSS JOIN temp_query_embedding t
        WHERE e.embedding IS NOT NULL
    """
    search_service.cursor.execute(count_sql_no_threshold)
    count_no_threshold = search_service.cursor.fetchone()[0]
    print(f"Count without threshold: {count_no_threshold}")
    
    # Test with threshold only
    count_sql_threshold_only = f"""
        SELECT COUNT(DISTINCT e.requestid)
        FROM request_embeddings e
        CROSS JOIN temp_query_embedding t
        WHERE e.embedding IS NOT NULL
        AND (1 - (e.embedding <=> t.embedding)) >= {similarity_threshold}
    """
    search_service.cursor.execute(count_sql_threshold_only)
    count_threshold_only = search_service.cursor.fetchone()[0]
    print(f"Count with threshold only: {count_threshold_only}")
    
    search_service.close()

if __name__ == "__main__":
    debug_count_query()

