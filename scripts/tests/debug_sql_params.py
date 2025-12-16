"""Debug SQL params issue."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from dotenv import load_dotenv

load_dotenv()

def debug_sql():
    """Debug SQL construction."""
    search_service = SearchService()
    search_service.connect_db()
    
    query = "בקשות מאור גלילי מסוג 4"
    
    # Parse
    parsed = search_service.query_parser.parse(query)
    entities = parsed.get('entities', {})
    
    print(f"Entities: {entities}")
    print()
    
    # Build filters manually to see what happens
    sql_filters = []
    filter_params = []
    
    if 'type_id' in entities:
        type_id = entities['type_id']
        sql_filters.append("r.requesttypeid::TEXT = %s::TEXT")
        filter_params.append(str(type_id))
        print(f"Added type_id filter: {sql_filters[-1]}")
        print(f"Added param: {filter_params[-1]}")
    
    print(f"\nsql_filters: {sql_filters}")
    print(f"filter_params: {filter_params}")
    
    request_filter_sql = ""
    if sql_filters:
        request_filter_sql = "WHERE " + " AND ".join(sql_filters)
        print(f"\nrequest_filter_sql: {request_filter_sql}")
    
    embedding_where = "WHERE e.embedding IS NOT NULL"
    join_sql = ""
    if request_filter_sql:
        join_sql = "INNER JOIN requests r ON e.requestid = r.requestid"
        embedding_where += " AND " + request_filter_sql.replace("WHERE ", "")
        print(f"\nembedding_where: {embedding_where}")
        print(f"join_sql: {join_sql}")
    
    # Check for %s in embedding_where
    placeholder_count = embedding_where.count('%s')
    print(f"\nPlaceholders in embedding_where: {placeholder_count}")
    print(f"filter_params length: {len(filter_params)}")
    
    if placeholder_count != len(filter_params):
        print(f"❌ MISMATCH: {placeholder_count} placeholders but {len(filter_params)} params!")
    else:
        print(f"✅ Match: {placeholder_count} placeholders = {len(filter_params)} params")
    
    search_service.close()

if __name__ == "__main__":
    debug_sql()

