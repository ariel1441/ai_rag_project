"""
Check if we're missing important fields in embeddings.
Specifically check updatedby, createdby, and other name fields.
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
print("Check Missing Fields in Embeddings")
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
    
    # Check what fields we currently use
    print("Step 1: Fields we currently use in embeddings...")
    print("  (from combine_text_fields function)")
    print("  - projectname")
    print("  - projectdesc")
    print("  - areadesc")
    print("  - remarks")
    print("  - requestjobshortdescription")
    print("  - requeststatusid")
    print("  - requesttypeid")
    print()
    
    # Check for "אריאל" in different fields
    print("Step 2: Check where 'אריאל' appears in requests table...")
    print()
    
    # List of fields that might contain names
    name_fields = [
        'updatedby', 'createdby', 
        'responsibleemployeename', 'responsibleemployeerolename',
        'contactfirstname', 'contactlastname',
        'metahnen_contactname', 'kabalan_contactname', 'yazam_contactname'
    ]
    
    found_in_fields = {}
    
    for field in name_fields:
        try:
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM requests 
                WHERE {field} LIKE '%אריאל%';
            """)
            count = cursor.fetchone()[0]
            if count > 0:
                found_in_fields[field] = count
                print(f"  ✅ '{field}': {count} requests")
        except Exception as e:
            # Field might not exist or have different name
            pass
    
    print()
    
    # Show examples
    if found_in_fields:
        print("Step 3: Examples of requests with 'אריאל' in these fields...")
        print()
        
        for field, count in found_in_fields.items():
            cursor.execute(f"""
                SELECT requestid, {field}
                FROM requests 
                WHERE {field} LIKE '%אריאל%'
                LIMIT 3;
            """)
            examples = cursor.fetchall()
            print(f"  Field: {field} ({count} total)")
            for req_id, value in examples:
                print(f"    Request {req_id}: {value}")
            print()
    
    # Check if these fields are in embeddings
    print("Step 4: Check if these fields are in embeddings...")
    print()
    
    if found_in_fields:
        # Check a request that has "אריאל" in updatedby/createdby
        for field in found_in_fields.keys():
            cursor.execute(f"""
                SELECT requestid, {field}
                FROM requests 
                WHERE {field} LIKE '%אריאל%'
                LIMIT 1;
            """)
            example = cursor.fetchone()
            if example:
                req_id, field_value = example
                print(f"  Request {req_id} has '{field_value}' in {field}")
                
                # Check if this appears in embeddings
                cursor.execute("""
                    SELECT text_chunk
                    FROM request_embeddings
                    WHERE requestid = %s;
                """, (str(req_id),))
                
                emb_texts = cursor.fetchall()
                found_in_embedding = False
                for emb_text in emb_texts:
                    if field_value and field_value in emb_text[0]:
                        found_in_embedding = True
                        break
                
                if found_in_embedding:
                    print(f"    ✅ Found in embedding!")
                else:
                    print(f"    ❌ NOT found in embedding!")
                    print(f"    ⚠️ This is why search doesn't find it!")
                print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    
    if found_in_fields:
        print("⚠️ PROBLEM IDENTIFIED:")
        print()
        print("  We're NOT including these fields in embeddings:")
        for field in found_in_fields.keys():
            print(f"    - {field} ({found_in_fields[field]} requests)")
        print()
        print("  This means:")
        print("    - Requests updated/created by 'אריאל בן עקיבא' exist")
        print("    - But they're NOT in the embeddings")
        print("    - So search can't find them!")
        print()
        print("  Solution:")
        print("    - Update combine_text_fields() to include these fields")
        print("    - Regenerate embeddings")
        print("    - Then search will find them!")
    else:
        print("✅ No issues found - all relevant fields are included")
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)

