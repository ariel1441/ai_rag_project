"""
Check if Hebrew data is stored correctly in database.
This will help us determine if it's a data issue or display issue.
"""
import psycopg2
import os
import sys

# Try to fix encoding
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
print("Check Hebrew Data in Database")
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

try:
    conn = psycopg2.connect(host=host, port=int(port), database=database, user=user, password=password)
    cursor = conn.cursor()
    
    # Check how Hebrew is stored
    print("Checking Hebrew text in database...")
    print()
    
    cursor.execute("""
        SELECT requestid, text_chunk
        FROM request_embeddings
        WHERE text_chunk LIKE '%אלינור%'
        LIMIT 5;
    """)
    
    results = cursor.fetchall()
    
    print("Sample requests with 'אלינור':")
    print()
    
    for req_id, text_chunk in results:
        print(f"Request {req_id}:")
        print(f"  Text Chunk (raw bytes): {repr(text_chunk[:50])}")
        print(f"  Text Chunk (display): {text_chunk[:100]}")
        print()
    
    # Check byte representation
    print("=" * 70)
    print("Byte Analysis")
    print("=" * 70)
    print()
    
    if results:
        sample_text = results[0][1]  # text_chunk
        if sample_text:
            print(f"Sample text: {sample_text}")
            print(f"Bytes (hex): {sample_text.encode('utf-8').hex()}")
            print(f"Character codes: {[ord(c) for c in sample_text[:10]]}")
            print()
            
            # Check if it's stored correctly
            expected = "אלינור"
            if expected in sample_text:
                print("✅ Text contains 'אלינור' correctly!")
                print("   Data is stored correctly in database.")
                print("   Issue is DISPLAY only (RTL rendering).")
            else:
                # Check if it's reversed
                reversed_text = sample_text[::-1]
                if expected in reversed_text:
                    print("⚠️ Text is stored REVERSED in database!")
                    print("   This is a data issue, not display.")
                else:
                    print("❓ Text format unclear")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("CONCLUSION")
print("=" * 70)
print()
print("If data shows 'אלינור' correctly above:")
print("  → Data is CORRECT, issue is RTL display in terminal")
print()
print("If data shows 'רונילא' (reversed):")
print("  → Data is WRONG, needs to be fixed in database")
print()

