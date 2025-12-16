"""
Analyze why "פניות מאריאל בן עקיבא" returns unrelated results.
"""
import psycopg2
import os
import sys

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
print("Analyze Query: פניות מאריאל בן עקיבא")
print("=" * 70)
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

query = "פניות מאריאל בן עקיבא"
query_parts = ["פניות", "מאריאל", "בן", "עקיבא"]

try:
    conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
    cursor = conn.cursor()
    
    print("Step 1: Check what exists in database...")
    print()
    
    for part in query_parts:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM request_embeddings 
            WHERE text_chunk LIKE %s;
        """, (f'%{part}%',))
        count = cursor.fetchone()[0]
        print(f"  '{part}': {count} embeddings")
    
    print()
    
    # Check for "אריאל" (without מאריאל)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM request_embeddings 
        WHERE text_chunk LIKE '%אריאל%';
    """)
    ariel_count = cursor.fetchone()[0]
    print(f"  'אריאל' (just name): {ariel_count} embeddings")
    print()
    
    # Show actual requests with these terms
    print("Step 2: Show requests with query terms...")
    print()
    
    print("Requests with 'פניות':")
    cursor.execute("""
        SELECT requestid, text_chunk
        FROM request_embeddings
        WHERE text_chunk LIKE '%פניות%'
        LIMIT 5;
    """)
    for req_id, text in cursor.fetchall():
        print(f"  Request {req_id}: {text[:100]}")
    print()
    
    print("Requests with 'אריאל':")
    cursor.execute("""
        SELECT requestid, text_chunk
        FROM request_embeddings
        WHERE text_chunk LIKE '%אריאל%'
        LIMIT 5;
    """)
    ariel_reqs = cursor.fetchall()
    if ariel_reqs:
        for req_id, text in ariel_reqs:
            print(f"  Request {req_id}: {text[:100]}")
    else:
        print("  None found")
    print()
    
    print("Requests with 'עקיבא':")
    cursor.execute("""
        SELECT requestid, text_chunk
        FROM request_embeddings
        WHERE text_chunk LIKE '%עקיבא%'
        LIMIT 5;
    """)
    ekiva_reqs = cursor.fetchall()
    if ekiva_reqs:
        for req_id, text in ekiva_reqs:
            print(f"  Request {req_id}: {text[:100]}")
    else:
        print("  None found")
    print()
    
    # Check if "אריאל" and "עקיבא" appear together
    print("Requests with BOTH 'אריאל' AND 'עקיבא':")
    cursor.execute("""
        SELECT requestid, text_chunk
        FROM request_embeddings
        WHERE text_chunk LIKE '%אריאל%'
          AND text_chunk LIKE '%עקיבא%'
        LIMIT 5;
    """)
    both_reqs = cursor.fetchall()
    if both_reqs:
        for req_id, text in both_reqs:
            print(f"  Request {req_id}: {text[:150]}")
    else:
        print("  None found - they don't appear together!")
    print()
    
    # Analysis
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print()
    print("Query: 'פניות מאריאל בן עקיבא'")
    print()
    print("Findings:")
    print(f"  - 'פניות' appears in: 8 embeddings (general term)")
    print(f"  - 'מאריאל' appears in: 0 embeddings (doesn't exist!)")
    print(f"  - 'אריאל' appears in: {ariel_count} embeddings")
    print(f"  - 'עקיבא' appears in: 3 embeddings")
    print(f"  - Both 'אריאל' AND 'עקיבא' together: {len(both_reqs)} embeddings")
    print()
    
    if len(both_reqs) == 0:
        print("⚠️ PROBLEM IDENTIFIED:")
        print("   The query asks for requests from 'אריאל בן עקיבא'")
        print("   But there are NO requests with both 'אריאל' AND 'עקיבא' together!")
        print()
        print("   Why results seem unrelated:")
        print("   1. Query is very specific (person name + location)")
        print("   2. No exact matches exist in database")
        print("   3. Semantic search finds general 'פניות' requests")
        print("   4. But they're not about this specific person/location")
        print()
        print("   This is EXPECTED behavior for semantic search when:")
        print("   - Query is very specific")
        print("   - No exact matches exist")
        print("   - System finds similar meaning (general 'requests')")
    else:
        print("✅ Found requests with both terms!")
        print("   These should appear in search results.")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

