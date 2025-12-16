"""Generate test queries with expected results from database."""
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from dotenv import load_dotenv
import psycopg2
from pgvector.psycopg2 import register_vector

load_dotenv()

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5433")),
        database=os.getenv("POSTGRES_DATABASE", "ai_requests_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD")
    )

def get_expected_counts():
    """Get expected counts from database for test queries."""
    conn = get_db_connection()
    register_vector(conn)
    cursor = conn.cursor()
    
    test_queries = []
    
    # 1. Single person queries
    print("Checking person queries...")
    persons = [
        ("אור גלילי", "מאור גלילי"),
        ("יניב ליבוביץ", "מיניב ליבוביץ"),
    ]
    
    for person_name, query_name in persons:
        cursor.execute("""
            SELECT COUNT(DISTINCT requestid)
            FROM requests
            WHERE 
                LOWER(COALESCE(updatedby, '')) LIKE %s OR
                LOWER(COALESCE(createdby, '')) LIKE %s OR
                LOWER(COALESCE(responsibleemployeename, '')) LIKE %s OR
                projectname LIKE %s
        """, (f'%{person_name}%', f'%{person_name}%', f'%{person_name}%', f'%{person_name}%'))
        count = cursor.fetchone()[0]
        test_queries.append({
            'query': f'פניות {query_name}',
            'type': 'Single Person',
            'expected_count': count,
            'expected_range': f'{max(0, int(count * 0.5))}-{int(count * 2)}',
            'description': f'Should return requests with {person_name} in person fields or project name'
        })
    
    # 2. Single type queries
    print("Checking type queries...")
    cursor.execute("""
        SELECT requesttypeid, COUNT(*) as cnt
        FROM requests
        GROUP BY requesttypeid
        ORDER BY cnt DESC
        LIMIT 3
    """)
    types = cursor.fetchall()
    for type_id, count in types:
        test_queries.append({
            'query': f'בקשות מסוג {type_id}',
            'type': 'Single Type',
            'expected_count': count,
            'expected_range': f'{max(0, int(count * 0.5))}-{int(count * 2)}',
            'description': f'Should return requests with type_id = {type_id}'
        })
    
    # 3. Single status queries
    print("Checking status queries...")
    cursor.execute("""
        SELECT requeststatusid, COUNT(*) as cnt
        FROM requests
        GROUP BY requeststatusid
        ORDER BY cnt DESC
        LIMIT 3
    """)
    statuses = cursor.fetchall()
    for status_id, count in statuses:
        test_queries.append({
            'query': f'בקשות בסטטוס {status_id}',
            'type': 'Single Status',
            'expected_count': count,
            'expected_range': f'{max(0, int(count * 0.5))}-{int(count * 2)}',
            'description': f'Should return requests with status_id = {status_id}'
        })
    
    # 4. Multiple entity queries (AND logic)
    print("Checking multiple entity combinations...")
    
    # Person + Type
    for person_name, query_name in persons[:1]:  # Just test first person
        for type_id, _ in types[:1]:  # Just test first type
            cursor.execute("""
                SELECT COUNT(DISTINCT r.requestid)
                FROM requests r
                WHERE r.requesttypeid::TEXT = %s::TEXT
                AND (
                    LOWER(COALESCE(r.updatedby, '')) LIKE %s OR
                    LOWER(COALESCE(r.createdby, '')) LIKE %s OR
                    LOWER(COALESCE(r.responsibleemployeename, '')) LIKE %s OR
                    r.projectname LIKE %s
                )
            """, (str(type_id), f'%{person_name}%', f'%{person_name}%', f'%{person_name}%', f'%{person_name}%'))
            db_count = cursor.fetchone()[0]
            
            # Get single person count for comparison
            cursor.execute("""
                SELECT COUNT(DISTINCT requestid)
                FROM requests
                WHERE 
                    LOWER(COALESCE(updatedby, '')) LIKE %s OR
                    LOWER(COALESCE(createdby, '')) LIKE %s OR
                    LOWER(COALESCE(responsibleemployeename, '')) LIKE %s OR
                    projectname LIKE %s
            """, (f'%{person_name}%', f'%{person_name}%', f'%{person_name}%', f'%{person_name}%'))
            single_count = cursor.fetchone()[0]
            
            test_queries.append({
                'query': f'בקשות {query_name} מסוג {type_id}',
                'type': 'Multiple (Person + Type)',
                'expected_count': db_count,
                'expected_range': f'{max(0, int(db_count * 0.5))}-{int(db_count * 2)}' if db_count > 0 else '0',
                'description': f'Should return FEWER than single person query ({single_count}). AND logic: both person AND type must match.',
                'should_be_less_than': single_count
            })
    
    # Person + Status
    for person_name, query_name in persons[:1]:
        for status_id, _ in statuses[:1]:
            cursor.execute("""
                SELECT COUNT(DISTINCT r.requestid)
                FROM requests r
                WHERE r.requeststatusid::TEXT = %s::TEXT
                AND (
                    LOWER(COALESCE(r.updatedby, '')) LIKE %s OR
                    LOWER(COALESCE(r.createdby, '')) LIKE %s OR
                    LOWER(COALESCE(r.responsibleemployeename, '')) LIKE %s OR
                    r.projectname LIKE %s
                )
            """, (str(status_id), f'%{person_name}%', f'%{person_name}%', f'%{person_name}%', f'%{person_name}%'))
            db_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(DISTINCT requestid)
                FROM requests
                WHERE 
                    LOWER(COALESCE(updatedby, '')) LIKE %s OR
                    LOWER(COALESCE(createdby, '')) LIKE %s OR
                    LOWER(COALESCE(responsibleemployeename, '')) LIKE %s OR
                    projectname LIKE %s
            """, (f'%{person_name}%', f'%{person_name}%', f'%{person_name}%', f'%{person_name}%'))
            single_count = cursor.fetchone()[0]
            
            test_queries.append({
                'query': f'פניות {query_name} בסטטוס {status_id}',
                'type': 'Multiple (Person + Status)',
                'expected_count': db_count,
                'expected_range': f'{max(0, int(db_count * 0.5))}-{int(db_count * 2)}' if db_count > 0 else '0',
                'description': f'Should return FEWER than single person query ({single_count}). AND logic: both person AND status must match.',
                'should_be_less_than': single_count
            })
    
    cursor.close()
    conn.close()
    
    return test_queries

def generate_test_guide():
    """Generate comprehensive test guide."""
    print("=" * 80)
    print("GENERATING TEST GUIDE WITH EXPECTED RESULTS")
    print("=" * 80)
    print()
    
    queries = get_expected_counts()
    
    print("TEST QUERIES AND EXPECTED RESULTS")
    print("=" * 80)
    print()
    
    # Group by type
    by_type = {}
    for q in queries:
        q_type = q['type']
        if q_type not in by_type:
            by_type[q_type] = []
        by_type[q_type].append(q)
    
    for q_type in ['Single Person', 'Single Type', 'Single Status', 'Multiple (Person + Type)', 'Multiple (Person + Status)']:
        if q_type not in by_type:
            continue
        
        print(f"\n## {q_type}")
        print("-" * 80)
        
        for i, q in enumerate(by_type[q_type], 1):
            print(f"\n{i}. Query: {q['query']}")
            print(f"   Expected Count: {q['expected_count']} (acceptable range: {q['expected_range']})")
            print(f"   Description: {q['description']}")
            if 'should_be_less_than' in q:
                print(f"   ⚠️  IMPORTANT: Should be LESS than {q['should_be_less_than']} (AND logic test)")
            print(f"   ✅ What to check:")
            print(f"      - Count matches or is close to expected")
            print(f"      - Count >= returned results (never less)")
            print(f"      - Results are relevant")
    
    print("\n" + "=" * 80)
    print("ADDITIONAL EDGE CASE TESTS")
    print("=" * 80)
    print()
    
    edge_cases = [
        {
            'query': 'בקשה מאור גלילי',
            'description': 'Singular form - should work (may return different count than plural)',
            'check': 'Count should be reasonable, not 0'
        },
        {
            'query': 'תיאום תכנון',
            'description': 'General query (NOT a person) - should NOT be detected as person',
            'check': 'Should return results, intent should NOT be "person"'
        },
        {
            'query': 'כמה פניות יש מאור גלילי?',
            'description': 'Count query with person',
            'check': 'Should return count, not full list'
        },
        {
            'query': 'פניות דומות ל221000226',
            'description': 'Similar requests query',
            'check': 'Should return similar requests to request ID 221000226'
        },
    ]
    
    for i, case in enumerate(edge_cases, 1):
        print(f"{i}. Query: {case['query']}")
        print(f"   Description: {case['description']}")
        print(f"   ✅ What to check: {case['check']}")
        print()
    
    print("=" * 80)
    print("TESTING CHECKLIST")
    print("=" * 80)
    print()
    print("For each query, verify:")
    print("  ✅ Count is displayed correctly (not 0 when results exist)")
    print("  ✅ Count >= returned results (never less)")
    print("  ✅ Results are relevant to the query")
    print("  ✅ Multiple entity queries return FEWER results (AND logic)")
    print("  ✅ Person names don't include type/status patterns")
    print("  ✅ No errors in terminal/console")
    print()

if __name__ == "__main__":
    generate_test_guide()

