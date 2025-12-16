"""
Debug script to check how "אור גלילי" is actually stored in the database.
"""
import os
import sys
from pathlib import Path
import psycopg2

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

def check_or_galili():
    """Check how אור גלילי is stored in database."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")
    database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")
    
    conn = psycopg2.connect(
        host=host, port=int(port), database=database,
        user=user, password=password
    )
    cursor = conn.cursor()
    
    print("=" * 80)
    print("CHECKING HOW 'אור גלילי' IS STORED IN DATABASE")
    print("=" * 80)
    print()
    
    # Check in person fields
    print("1. Checking in person fields (updatedby, createdby, responsibleemployeename):")
    cursor.execute("""
        SELECT COUNT(DISTINCT requestid)
        FROM requests
        WHERE 
            LOWER(COALESCE(updatedby, '')) LIKE '%אור גלילי%' OR
            LOWER(COALESCE(createdby, '')) LIKE '%אור גלילי%' OR
            LOWER(COALESCE(responsibleemployeename, '')) LIKE '%אור גלילי%'
    """)
    count_person = cursor.fetchone()[0]
    print(f"   Found: {count_person} requests")
    print()
    
    # Check in projectname
    print("2. Checking in projectname:")
    cursor.execute("""
        SELECT COUNT(DISTINCT requestid)
        FROM requests
        WHERE LOWER(COALESCE(projectname, '')) LIKE '%אור גלילי%'
    """)
    count_project = cursor.fetchone()[0]
    print(f"   Found: {count_project} requests")
    print()
    
    # Check with just "אור" (first name only)
    print("3. Checking for just 'אור' in person fields:")
    cursor.execute("""
        SELECT COUNT(DISTINCT requestid)
        FROM requests
        WHERE 
            LOWER(COALESCE(updatedby, '')) LIKE '%אור%' OR
            LOWER(COALESCE(createdby, '')) LIKE '%אור%' OR
            LOWER(COALESCE(responsibleemployeename, '')) LIKE '%אור%'
    """)
    count_or_only = cursor.fetchone()[0]
    print(f"   Found: {count_or_only} requests")
    print()
    
    # Check with "גלילי" (last name only)
    print("4. Checking for just 'גלילי' in person fields:")
    cursor.execute("""
        SELECT COUNT(DISTINCT requestid)
        FROM requests
        WHERE 
            LOWER(COALESCE(updatedby, '')) LIKE '%גלילי%' OR
            LOWER(COALESCE(createdby, '')) LIKE '%גלילי%' OR
            LOWER(COALESCE(responsibleemployeename, '')) LIKE '%גלילי%'
    """)
    count_galili_only = cursor.fetchone()[0]
    print(f"   Found: {count_galili_only} requests")
    print()
    
    # Show sample records
    print("5. Sample records with 'אור' in person fields:")
    cursor.execute("""
        SELECT DISTINCT requestid, updatedby, createdby, responsibleemployeename, projectname
        FROM requests
        WHERE 
            LOWER(COALESCE(updatedby, '')) LIKE '%אור%' OR
            LOWER(COALESCE(createdby, '')) LIKE '%אור%' OR
            LOWER(COALESCE(responsibleemployeename, '')) LIKE '%אור%'
        LIMIT 10
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"   RequestID: {row[0]}")
        print(f"   UpdatedBy: {row[1]}")
        print(f"   CreatedBy: {row[2]}")
        print(f"   Responsible: {row[3]}")
        print(f"   ProjectName: {row[4]}")
        print()
    
    # Check in projectname samples
    print("6. Sample records with 'אור גלילי' in projectname:")
    cursor.execute("""
        SELECT DISTINCT requestid, projectname, updatedby, createdby
        FROM requests
        WHERE LOWER(COALESCE(projectname, '')) LIKE '%אור גלילי%'
        LIMIT 10
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"   RequestID: {row[0]}")
        print(f"   ProjectName: {row[1]}")
        print(f"   UpdatedBy: {row[2]}")
        print(f"   CreatedBy: {row[3]}")
        print()
    
    cursor.close()
    conn.close()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Person fields (updatedby/createdby/responsible): {count_person}")
    print(f"Projectname: {count_project}")
    print(f"Just 'אור' in person fields: {count_or_only}")
    print(f"Just 'גלילי' in person fields: {count_galili_only}")
    print()
    print("CONCLUSION:")
    if count_person == 0 and count_project > 0:
        print("  ❌ 'אור גלילי' is NOT in person fields, but IS in projectname")
        print("  ✅ This explains why search finds it (searches all fields) but DB count is 0")
    elif count_person > 0:
        print("  ✅ 'אור גלילי' IS in person fields")
        print("  ⚠️  But the test query might be wrong (case sensitivity, spacing, etc.)")
    else:
        print("  ❌ 'אור גלילי' is NOT found anywhere in the database")
        print("  ⚠️  Search is finding semantically similar results, not exact matches")

if __name__ == "__main__":
    check_or_galili()

