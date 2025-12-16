"""
Check actual data in requests table for specific request IDs.
This helps verify why search results appear even if they don't match the query.
"""
import psycopg2
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Fix encoding
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 >nul 2>&1')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except:
        pass

# Connection
host = os.getenv("POSTGRES_HOST", "localhost")
port = os.getenv("POSTGRES_PORT", "5433")
database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
user = os.getenv("POSTGRES_USER", "postgres")
password = os.getenv("POSTGRES_PASSWORD")

if not password:
    print("ERROR: POSTGRES_PASSWORD not in .env!")
    exit(1)

# Request IDs to check (as strings since requestid is text in database)
request_ids = ['212000095', '229000076', '229000098', '229000096', '229000080', '229000087', '229000095', '229000094']

try:
    conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
    cursor = conn.cursor()
    
    print("=" * 80)
    print("Checking Request Data in Database")
    print("=" * 80)
    print()
    
    placeholders = ','.join(['%s'] * len(request_ids))
    cursor.execute(f"""
        SELECT 
            requestid, 
            projectname, 
            updatedby, 
            createdby, 
            responsibleemployeename,
            contactfirstname,
            contactlastname,
            projectdesc
        FROM requests
        WHERE requestid IN ({placeholders})
        ORDER BY requestid;
    """, request_ids)
    
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} requests")
    print()
    print("=" * 80)
    print("REQUEST DATA")
    print("=" * 80)
    print()
    
    search_term = "אריאל בן עקיבא"
    
    for row in rows:
        req_id, projectname, updatedby, createdby, responsible, contactfirst, contactlast, projectdesc = row
        print(f"Request ID: {req_id}")
        print("-" * 80)
        
        # Check if search term appears
        matches = []
        if updatedby and search_term in str(updatedby):
            matches.append("✓ Updated By")
        if createdby and search_term in str(createdby):
            matches.append("✓ Created By")
        if responsible and search_term in str(responsible):
            matches.append("✓ Responsible")
        if contactfirst and search_term in str(contactfirst):
            matches.append("✓ Contact First Name")
        if contactlast and search_term in str(contactlast):
            matches.append("✓ Contact Last Name")
        if projectname and search_term in str(projectname):
            matches.append("✓ Project Name")
        if projectdesc and search_term in str(projectdesc):
            matches.append("✓ Project Desc")
        
        if matches:
            print(f"  🎯 MATCHES: {', '.join(matches)}")
        else:
            print(f"  ❌ NO MATCH - Why is this in results?")
        
        print(f"  Project: {projectname or 'NULL'}")
        print(f"  Updated By: {updatedby or 'NULL'}")
        print(f"  Created By: {createdby or 'NULL'}")
        print(f"  Responsible: {responsible or 'NULL'}")
        print(f"  Contact: {contactfirst or ''} {contactlast or ''}".strip() or 'NULL')
        print()
    
    print("=" * 80)
    print("Checking Embeddings Table")
    print("=" * 80)
    print()
    
    # Check how many embeddings exist
    cursor.execute("SELECT COUNT(*) FROM request_embeddings;")
    total_embeddings = cursor.fetchone()[0]
    print(f"Total embeddings in database: {total_embeddings:,}")
    print()
    
    # Check a sample embedding text_chunk to see if it has updatedby
    cursor.execute("""
        SELECT requestid, chunk_index, LEFT(text_chunk, 200) as preview
        FROM request_embeddings
        WHERE requestid IN ('212000095', '229000080')
        ORDER BY requestid, chunk_index
        LIMIT 5;
    """)
    
    sample_chunks = cursor.fetchall()
    print("Sample embedding chunks (first 200 chars):")
    print()
    for req_id, chunk_idx, preview in sample_chunks:
        print(f"Request {req_id}, Chunk {chunk_idx}:")
        print(f"  {preview}")
        has_updated_by = "Updated By" in preview or "updatedby" in preview.lower()
        if has_updated_by:
            print("  ✓ Contains 'Updated By' field")
        else:
            print("  ❌ Does NOT contain 'Updated By' field")
        print()
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

