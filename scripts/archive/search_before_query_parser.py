"""
Main search script - uses query parser + hybrid method (field-specific + semantic).
This is the recommended search script to use.
"""
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
from pgvector.psycopg2 import register_vector
import os
import sys
import re
import json
from pathlib import Path

# Import query parser
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.query_parser import parse_query

# Fix Hebrew RTL display - reverses Hebrew text for correct display in LTR terminals
def fix_hebrew_rtl(text):
    """
    Fix Hebrew RTL display for LTR terminals.
    Reverses Hebrew text segments so they display correctly.
    Data in database is CORRECT - this is display only.
    """
    if not text:
        return text
    
    # Hebrew Unicode range: \u0590-\u05FF
    # Split text into Hebrew and non-Hebrew segments
    pattern = r'([\u0590-\u05FF]+|[^\u0590-\u05FF]+)'
    parts = re.findall(pattern, str(text))
    
    result = []
    for part in parts:
        # If Hebrew text, reverse it for display
        if re.match(r'[\u0590-\u05FF]+', part):
            result.append(part[::-1])
        else:
            result.append(part)
    
    return ''.join(result)

# Fix encoding
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 >nul 2>&1')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

print("=" * 70)
print("Semantic Search (Query Parser + Hybrid: Field-Specific + Semantic)")
print("=" * 70)
print()
print("You can search with ANY query - it will understand intent and find relevant requests!")
print("The system uses query parsing to understand what you're looking for,")
print("then combines field-specific search with semantic ranking for best results.")
print()
print("Examples:")
print("  - 'פניות מאור גלילי' (finds requests from person)")
print("  - 'בקשות מסוג 4' (finds requests of type 4)")
print("  - 'פרויקט אלינור' (finds requests for project)")
print("  - 'אלינור' (general semantic search)")
print()

# Connection
host = os.getenv("POSTGRES_HOST", "localhost")
port = os.getenv("POSTGRES_PORT", "5433")
database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD")

if not password:
    print("ERROR: POSTGRES_PASSWORD not in .env!")
    exit(1)

# Get query from user
query = input("Enter your search query: ").strip()
if not query:
    print("No query provided. Exiting.")
    exit(0)

# Fix query display (for terminal - data is correct)
query_display = fix_hebrew_rtl(query)

print()
print(f"Searching for: '{query_display}'")
print()

# Load search config
config_path = Path(__file__).parent.parent.parent / "config" / "search_config.json"
config = None
if config_path.exists():
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✓ Loaded search configuration")
    except Exception as e:
        print(f"⚠ Could not load config: {e}, using defaults")
else:
    print("⚠ Config file not found, using defaults")

# Parse query to understand intent
print("Parsing query...")
parsed = parse_query(query, config)
print(f"✓ Intent: {parsed['intent']}")
if parsed['entities']:
    print(f"✓ Entities: {parsed['entities']}")
if parsed['target_fields']:
    print(f"✓ Target fields: {', '.join(parsed['target_fields'][:3])}...")
print()

try:
    conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
    register_vector(conn)
    cursor = conn.cursor()
    
    # Apply filters from parser (e.g., type_id, status_id)
    sql_filters = []
    filter_params = []
    
    if 'type_id' in parsed['entities']:
        type_id = parsed['entities']['type_id']
        sql_filters.append("r.requesttypeid = %s")
        filter_params.append(type_id)
        print(f"✓ Filter: requesttypeid = {type_id}")
    
    if 'status_id' in parsed['entities']:
        status_id = parsed['entities']['status_id']
        sql_filters.append("r.requeststatusid = %s")
        filter_params.append(status_id)
        print(f"✓ Filter: requeststatusid = {status_id}")
    
    # Build WHERE clause for request filtering
    request_filter_sql = ""
    if sql_filters:
        request_filter_sql = "WHERE " + " AND ".join(sql_filters)
        print()
    
    # Generate embedding
    print("Generating embedding...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
    print(f"✓ Embedding generated: {len(query_embedding)} dimensions")
    print()
    
    # Insert into temp table
    print("Preparing search...")
    cursor.execute("""
        CREATE TEMP TABLE temp_query_embedding (
            id SERIAL PRIMARY KEY,
            embedding vector(384)
        );
    """)
    
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    cursor.execute("""
        INSERT INTO temp_query_embedding (embedding)
        VALUES (%s::vector);
    """, (embedding_str,))
    
    conn.commit()
    print("✓ Ready to search")
    print()
    
    # Build boost logic based on target fields and entities
    boost_cases = []
    boost_conditions = []
    
    # If we have target fields and entities, boost exact matches in those fields
    if parsed['target_fields'] and parsed['entities']:
        # Get entity value (person name, project name, etc.)
        entity_value = None
        if 'person_name' in parsed['entities']:
            entity_value = parsed['entities']['person_name']
        elif 'project_name' in parsed['entities']:
            entity_value = parsed['entities']['project_name']
        
        if entity_value:
            # Build boost for exact matches in target fields
            # Check if entity appears in text_chunk with field labels
            field_labels = {
                'updatedby': 'Updated By',
                'createdby': 'Created By',
                'responsibleemployeename': 'Responsible Employee',
                'contactfirstname': 'Contact First Name',
                'contactlastname': 'Contact Last Name',
                'projectname': 'Project',
                'projectdesc': 'Description'
            }
            
            for field in parsed['target_fields']:
                if field in field_labels:
                    label = field_labels[field]
                    # Boost if entity appears with this field label
                    boost_cases.append(f"WHEN e.text_chunk LIKE '%{label}: %{entity_value}%' THEN 2.0")
            
            # Also boost if entity appears anywhere in chunk (semantic match)
            boost_cases.append("WHEN e.text_chunk LIKE '%" + entity_value + "%' THEN 1.5")
    
    # Default boost
    boost_cases.append("ELSE 1.0")
    boost_sql = "CASE " + " ".join(boost_cases) + " END as boost"
    
    # Build WHERE clause for embedding search
    embedding_where = "WHERE e.embedding IS NOT NULL"
    
    # If we have request filters, join with requests table
    join_sql = ""
    if request_filter_sql:
        join_sql = """
            INNER JOIN requests r ON e.requestid = r.requestid
        """
        # Replace WHERE with AND in request_filter_sql
        embedding_where += " AND " + request_filter_sql.replace("WHERE ", "")
    
    # HYBRID SEARCH: Field-specific + Semantic ranking
    print("Searching database...")
    
    search_sql = f"""
        SELECT 
            e.requestid,
            e.chunk_index,
            LEFT(e.text_chunk, 250) as text_preview,
            1 - (e.embedding <=> t.embedding) as similarity,
            {boost_sql}
        FROM request_embeddings e
        {join_sql}
        CROSS JOIN temp_query_embedding t
        {embedding_where}
        ORDER BY (1 - (e.embedding <=> t.embedding)) * 
                 ({boost_sql}) DESC
        LIMIT 50;
    """
    
    if filter_params:
        cursor.execute(search_sql, tuple(filter_params))
    else:
        cursor.execute(search_sql)
    
    chunk_results = cursor.fetchall()
    
    print(f"✓ Found {len(chunk_results)} chunk results")
    print()
    
    if chunk_results:
        # Group by request ID - get best similarity per request
        request_scores = {}
        for req_id, chunk_idx, text_preview, similarity, boost in chunk_results:
            if req_id not in request_scores:
                request_scores[req_id] = {
                    'best_similarity': similarity,
                    'best_chunk': chunk_idx,
                    'boost': float(boost) if boost else 1.0
                }
            else:
                # Keep the best similarity
                if similarity > request_scores[req_id]['best_similarity']:
                    request_scores[req_id]['best_similarity'] = similarity
                    request_scores[req_id]['best_chunk'] = chunk_idx
        
        # Sort by similarity
        sorted_requests = sorted(
            request_scores.items(),
            key=lambda x: x[1]['best_similarity'] * x[1]['boost'],
            reverse=True
        )
        
        # Get unique request IDs (top 50 for filtering)
        unique_request_ids = [req_id for req_id, _ in sorted_requests[:50]]
        
        print(f"✓ Found {len(unique_request_ids)} unique requests")
        print()
        
        # Ask user what they want to see
        print("Display options:")
        print("  1. Request IDs only (quick)")
        print("  2. Full request details (detailed)")
        print()
        display_choice = input("Choose option (1 or 2, default=2): ").strip() or "2"
        
        # Fetch full request data
        if unique_request_ids:
            placeholders = ','.join(['%s'] * len(unique_request_ids))
            cursor.execute(f"""
                SELECT 
                    requestid, projectname, projectdesc, areadesc, remarks,
                    updatedby, createdby, responsibleemployeename,
                    contactfirstname, contactlastname, contactemail,
                    requesttypeid, requeststatusid, requeststatusdate
                FROM requests
                WHERE requestid IN ({placeholders})
                ORDER BY requestid;
            """, unique_request_ids)
            
            full_requests = cursor.fetchall()
            # Create a dict for quick lookup
            requests_dict = {req[0]: req for req in full_requests}
            
            # Filter results based on parser intent
            # If person query, only show requests where person name appears in target fields
            is_person_query = parsed['intent'] == 'person' and 'person_name' in parsed['entities']
            
            if is_person_query and display_choice != "1":
                # Filter: Only keep requests where person name appears in target fields
                person_name = parsed['entities']['person_name'].lower()
                filtered_request_ids = []
                for req_id in unique_request_ids:
                    if req_id in requests_dict:
                        req_data = requests_dict[req_id]
                        (_, _, _, _, _, updatedby, createdby, responsibleemployeename,
                         contactfirstname, contactlastname, _, _, _, _) = req_data
                        
                        # Check if person name appears in any target field
                        has_match = False
                        if updatedby and person_name in str(updatedby).lower():
                            has_match = True
                        if createdby and person_name in str(createdby).lower():
                            has_match = True
                        if responsibleemployeename and person_name in str(responsibleemployeename).lower():
                            has_match = True
                        if contactfirstname and person_name in str(contactfirstname).lower():
                            has_match = True
                        if contactlastname and person_name in str(contactlastname).lower():
                            has_match = True
                        
                        # Also check word-by-word match (for multi-word names)
                        if not has_match:
                            person_words = person_name.split()
                            for word in person_words:
                                if (updatedby and word in str(updatedby).lower()) or \
                                   (createdby and word in str(createdby).lower()) or \
                                   (responsibleemployeename and word in str(responsibleemployeename).lower()):
                                    has_match = True
                                    break
                        
                        if has_match:
                            filtered_request_ids.append(req_id)
                        # If no match but similarity is very high (>0.7), keep it (might be correct)
                        elif request_scores[req_id]['best_similarity'] > 0.7:
                            filtered_request_ids.append(req_id)
                
                # Update unique_request_ids to filtered list (but keep at least top 10)
                if len(filtered_request_ids) >= 3:
                    unique_request_ids = filtered_request_ids[:20]
                else:
                    # If too few results, show top 10 by similarity (might be correct)
                    unique_request_ids = [req_id for req_id, _ in sorted_requests[:10]]
        
        print()
        print("=" * 70)
        print("TOP RESULTS (Full Requests)")
        print("=" * 70)
        print()
        print("Note: Chunks are used for search, but results show FULL requests.")
        if parsed['intent'] != 'general':
            print(f"Note: Query intent detected as '{parsed['intent']}' - results filtered/boosted accordingly.")
        if is_person_query and display_choice != "1":
            print(f"Note: Filtered to show only requests where '{parsed['entities'].get('person_name', 'person name')}' appears in key fields.")
        print()
        
        if display_choice == "1":
            # Just show IDs
            print("Request IDs:")
            for i, req_id in enumerate(unique_request_ids, 1):
                score_info = request_scores[req_id]
                similarity = score_info['best_similarity']
                print(f"  {i}. Request {req_id} (Similarity: {similarity:.4f} = {similarity*100:.2f}%)")
        else:
            # Show full details
            for i, req_id in enumerate(unique_request_ids, 1):
                score_info = request_scores[req_id]
                similarity = score_info['best_similarity']
                boost = score_info['boost']
                adjusted_similarity = similarity * boost
                
                if req_id in requests_dict:
                    req_data = requests_dict[req_id]
                    (req_id_val, projectname, projectdesc, areadesc, remarks,
                     updatedby, createdby, responsibleemployeename,
                     contactfirstname, contactlastname, contactemail,
                     requesttypeid, requeststatusid, requeststatusdate) = req_data
                    
                    print(f"{i}. Request {req_id_val}")
                    print(f"   Similarity: {similarity:.4f} ({similarity*100:.2f}%)")
                    if boost > 1.0:
                        print(f"   Boosted: {adjusted_similarity:.4f} ({adjusted_similarity*100:.2f}%)")
                    print()
                    
                    # Check if search term appears in key fields
                    query_lower = query.lower()
                    matches = []
                    if updatedby and query_lower in str(updatedby).lower():
                        matches.append("Updated By")
                    if createdby and query_lower in str(createdby).lower():
                        matches.append("Created By")
                    if responsibleemployeename and query_lower in str(responsibleemployeename).lower():
                        matches.append("Responsible Employee")
                    if contactfirstname and query_lower in str(contactfirstname).lower():
                        matches.append("Contact First Name")
                    if projectname and query_lower in str(projectname).lower():
                        matches.append("Project Name")
                    
                    if matches:
                        print(f"   ✓ Found in: {', '.join(matches)}")
                        print()
                    
                    # Show key fields
                    print("   Key Fields:")
                    if projectname:
                        print(f"     Project: {fix_hebrew_rtl(str(projectname))}")
                    if updatedby:
                        print(f"     Updated By: {fix_hebrew_rtl(str(updatedby))}")
                    if createdby:
                        print(f"     Created By: {fix_hebrew_rtl(str(createdby))}")
                    if responsibleemployeename:
                        print(f"     Responsible: {fix_hebrew_rtl(str(responsibleemployeename))}")
                    if contactfirstname or contactlastname:
                        contact_name = f"{contactfirstname or ''} {contactlastname or ''}".strip()
                        if contact_name:
                            print(f"     Contact: {fix_hebrew_rtl(contact_name)}")
                    if requesttypeid:
                        print(f"     Type ID: {requesttypeid}")
                    if requeststatusid:
                        print(f"     Status ID: {requeststatusid}")
                    if projectdesc:
                        desc_preview = str(projectdesc)[:100] + "..." if len(str(projectdesc)) > 100 else str(projectdesc)
                        print(f"     Description: {fix_hebrew_rtl(desc_preview)}")
                    print()
                else:
                    print(f"{i}. Request {req_id} (Similarity: {similarity:.4f} = {similarity*100:.2f}%)")
                    print("   ⚠ Full request data not found in database")
                    print()
        
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Total unique requests: {len(unique_request_ids)}")
        if sorted_requests:
            best_sim = sorted_requests[0][1]['best_similarity']
            print(f"Best similarity: {best_sim:.4f} ({best_sim*100:.2f}%)")
        print()
        print("Note: Chunks are used for search (finding relevant requests),")
        print("      but results show FULL requests (not chunks).")
        print()
        print("Note: Hebrew text has been reversed for correct display.")
        print("      Data in database is CORRECT - this is display only.")
    else:
        print("⚠ No results found")
        print()
        print("This might mean:")
        print("  - No requests are semantically similar to your query")
        print("  - Try a different query or more specific terms")
    
    # Clean up
    cursor.execute("DROP TABLE IF EXISTS temp_query_embedding;")
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

