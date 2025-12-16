"""
Debug script to check why data analysis is showing incorrect values.
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=int(os.getenv("POSTGRES_PORT", "5433")),
    database=os.getenv("POSTGRES_DATABASE", "ai_requests_db"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD")
)

cursor = conn.cursor()

# Check if test table exists
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_name = 'test_requests'
    );
""")
table_exists = cursor.fetchone()[0]

if not table_exists:
    print("Test table doesn't exist. Creating it...")
    # Create a simple test table
    cursor.execute("DROP TABLE IF EXISTS test_requests CASCADE;")
    cursor.execute("""
        CREATE TABLE test_requests (
            id SERIAL PRIMARY KEY,
            project_name TEXT,
            description TEXT,
            notes TEXT
        );
    """)
    
    # Insert test data
    for i in range(100):
        cursor.execute("""
            INSERT INTO test_requests (project_name, description, notes)
            VALUES (%s, %s, %s);
        """, (
            f"Project {i}" if i < 80 else None,  # 80% coverage
            f"Description {i}" if i < 50 else None,  # 50% coverage
            f"Notes {i}" if i % 3 == 0 else None  # 33% coverage
        ))
    
    conn.commit()
    print("✓ Test table created with 100 rows")

# Test data fetching
print("\n" + "=" * 80)
print("TESTING DATA FETCHING")
print("=" * 80)

columns = ['project_name', 'description', 'notes']

for col in columns:
    print(f"\nColumn: {col}")
    
    # Test 1: Get all rows
    cursor.execute(f"SELECT COUNT(*) FROM test_requests;")
    total_rows = cursor.fetchone()[0]
    print(f"  Total rows: {total_rows}")
    
    # Test 2: Get non-null rows
    cursor.execute(f"SELECT COUNT(*) FROM test_requests WHERE {col} IS NOT NULL;")
    non_null_count = cursor.fetchone()[0]
    print(f"  Non-null rows: {non_null_count}")
    print(f"  Coverage: {non_null_count / total_rows * 100:.1f}%")
    
    # Test 3: Get sample data (like the analysis does)
    cursor.execute(f"""
        SELECT {col}
        FROM test_requests
        WHERE {col} IS NOT NULL
        LIMIT 200
    """)
    rows = cursor.fetchall()
    print(f"  Sample rows fetched: {len(rows)}")
    
    if rows:
        # Convert to strings
        values = [str(row[0]).strip() for row in rows if row[0] is not None and str(row[0]).strip()]
        print(f"  Values after filtering: {len(values)}")
        
        if values:
            # Check uniqueness
            unique_count = len(set(values))
            uniqueness = unique_count / len(values) * 100
            print(f"  Unique values: {unique_count}")
            print(f"  Uniqueness: {uniqueness:.1f}%")
            
            # Check avg length
            avg_length = sum(len(v) for v in values) / len(values)
            print(f"  Avg length: {avg_length:.1f} chars")
            
            # Show first few values
            print(f"  First 3 values: {values[:3]}")
        else:
            print("  ⚠️ No valid values after filtering!")
    else:
        print("  ⚠️ No rows fetched!")

# Test the actual analysis function
print("\n" + "=" * 80)
print("TESTING ACTUAL ANALYSIS FUNCTION")
print("=" * 80)

import sys
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from scripts.setup.intelligent_field_analysis import IntelligentFieldAnalyzer

analyzer = IntelligentFieldAnalyzer(cursor)

for col in columns:
    print(f"\nColumn: {col}")
    
    # Debug: Check what the function is actually getting
    cursor.execute(f"SELECT COUNT(*) FROM test_requests;")
    total = cursor.fetchone()[0]
    print(f"  Total table rows: {total}")
    
    cursor.execute(f"SELECT COUNT(*) FROM test_requests WHERE {col} IS NOT NULL;")
    non_null = cursor.fetchone()[0]
    print(f"  Non-null rows: {non_null}")
    
    cursor.execute(f"SELECT {col} FROM test_requests WHERE {col} IS NOT NULL LIMIT 5;")
    sample = cursor.fetchall()
    print(f"  Sample values (raw): {sample}")
    print(f"  Sample values (as strings): {[str(s[0]) for s in sample]}")
    print(f"  Sample values (stripped): {[str(s[0]).strip() for s in sample]}")
    
    result = analyzer.analyze_data_quality("test_requests", col, sample_size=100)
    print(f"  Coverage: {result['coverage']*100:.1f}%")
    print(f"  Uniqueness: {result['uniqueness']*100:.1f}%")
    print(f"  Diversity: {result['diversity']*100:.1f}%")
    print(f"  Avg Length: {result['avg_length']:.1f} chars")
    print(f"  Score: {result['score']:.3f}")
    if 'error' in result:
        print(f"  ERROR: {result['error']}")

cursor.close()
conn.close()

