"""
Test Intelligent Field Analysis with Example Request/Transaction Table

Creates a sample table with different naming conventions and tests the analysis.
"""
import psycopg2
import os
from dotenv import load_dotenv
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from scripts.setup.intelligent_field_analysis import analyze_table_fields

load_dotenv()


def create_test_table(cursor):
    """Create a test table with various naming conventions."""
    print("Creating test table 'test_requests'...")
    
    # Drop if exists
    cursor.execute("DROP TABLE IF EXISTS test_requests CASCADE;")
    
    # Create table with mixed naming conventions
    cursor.execute("""
        CREATE TABLE test_requests (
            -- Primary key
            request_id SERIAL PRIMARY KEY,
            
            -- Critical fields (different naming styles)
            project_name TEXT,           -- snake_case
            projectDesc TEXT,            -- camelCase
            ItemTitle TEXT,              -- PascalCase
            item_description TEXT,       -- snake_case
            remarks TEXT,                -- lowercase
            
            -- Important fields (different styles)
            created_date DATE,           -- snake_case
            updatedDate TIMESTAMP,       -- camelCase
            StatusId INTEGER,            -- PascalCase
            type_id INTEGER,             -- snake_case
            contact_email TEXT,          -- snake_case
            contactPhone TEXT,           -- camelCase
            
            -- Supporting fields
            additional_info TEXT,        -- snake_case
            notes TEXT,                  -- lowercase
            priority_level INTEGER,      -- snake_case
            
            -- Excluded fields (should be excluded)
            internal_id INTEGER,         -- Should be excluded
            user_uuid UUID,              -- Should be excluded
            password_hash TEXT,           -- Should be excluded
            
            -- Low priority fields
            coord_x DECIMAL,             -- Should be low priority
            coord_y DECIMAL,             -- Should be low priority
            
            -- Abbreviated fields (to test abbreviation expansion)
            proj_nm TEXT,                -- Should expand to project name
            desc_txt TEXT,               -- Should expand to description text
            emp_name TEXT,               -- Should expand to employee name
            cont_eml TEXT,               -- Should expand to contact email
            
            -- Custom/unknown fields (to test data-driven analysis)
            custom_field_xyz TEXT,        -- No pattern match, but good data
            item_text_long TEXT,          -- No pattern match, but good data
            main_content TEXT             -- No pattern match, but good data
        );
    """)
    
    print("✓ Table created")
    
    # Insert sample data
    print("Inserting sample data...")
    
    sample_data = []
    for i in range(100):
        sample_data.append((
            f"Project {i % 20}",                    # project_name (high uniqueness)
            f"Project Description {i}",              # projectDesc (high uniqueness)
            f"Item Title {i}",                        # ItemTitle (high uniqueness)
            f"Item description for request {i}",     # item_description (high uniqueness)
            f"Remarks for request {i}" if i % 3 == 0 else None,  # remarks (33% coverage)
            '2024-01-01',                            # created_date
            '2024-01-02',                            # updatedDate
            i % 5,                                   # StatusId (5 unique values)
            i % 3,                                   # type_id (3 unique values)
            f"user{i}@example.com",                  # contact_email (high uniqueness)
            f"+123456789{i:02d}",                    # contactPhone (high uniqueness)
            f"Additional info {i}" if i % 2 == 0 else None,  # additional_info (50% coverage)
            f"Notes {i}" if i % 4 == 0 else None,    # notes (25% coverage)
            i % 4,                                   # priority_level (4 unique values)
            i,                                       # internal_id (should be excluded)
            None,                                    # user_uuid (should be excluded)
            None,                                    # password_hash (should be excluded)
            i * 1.5,                                 # coord_x (should be low priority)
            i * 2.0,                                 # coord_y (should be low priority)
            f"Project {i % 20}",                      # proj_nm (abbreviation)
            f"Description text {i}",                 # desc_txt (abbreviation)
            f"Employee {i % 10}",                    # emp_name (abbreviation)
            f"contact{i}@example.com",               # cont_eml (abbreviation)
            f"Custom field value {i}",               # custom_field_xyz (no pattern, good data)
            f"Long text content for item {i} with detailed description",  # item_text_long (no pattern, good data)
            f"Main content for request {i}"         # main_content (no pattern, good data)
        ))
    
    cursor.executemany("""
        INSERT INTO test_requests (
            project_name, projectDesc, ItemTitle, item_description, remarks,
            created_date, updatedDate, StatusId, type_id, contact_email, contactPhone,
            additional_info, notes, priority_level,
            internal_id, user_uuid, password_hash,
            coord_x, coord_y,
            proj_nm, desc_txt, emp_name, cont_eml,
            custom_field_xyz, item_text_long, main_content
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """, sample_data)
    
    print(f"✓ Inserted {len(sample_data)} rows")


def run_analysis(cursor):
    """Run the intelligent field analysis."""
    print("\n" + "=" * 80)
    print("RUNNING INTELLIGENT FIELD ANALYSIS")
    print("=" * 80)
    
    result = analyze_table_fields(cursor, "test_requests", sample_size=100)
    
    if 'error' in result:
        print(f"ERROR: {result['error']}")
        return
    
    analysis = result['analysis']
    weights = result['weights']
    
    print(f"\nTable: {analysis['table_name']}")
    print(f"Total Rows: {analysis['total_rows']:,}")
    print(f"Sample Size: {analysis['sample_size']:,}")
    print(f"Columns Analyzed: {analysis['columns_analyzed']}")
    print(f"Columns Excluded: {analysis['columns_excluded']}")
    
    print("\n" + "-" * 80)
    print("WEIGHT SUGGESTIONS")
    print("-" * 80)
    
    print(f"\n🔴 3.0x (Critical): {len(weights['3.0x'])} fields")
    for field in weights['3.0x']:
        field_analysis = next((r for r in analysis['results'] if r['column'] == field), None)
        if field_analysis:
            reason = field_analysis.get('name_reason', 'N/A')
            coverage = field_analysis.get('data_analysis', {}).get('coverage', 0) * 100
            uniqueness = field_analysis.get('data_analysis', {}).get('uniqueness', 0) * 100
            avg_length = field_analysis.get('data_analysis', {}).get('avg_length', 0)
            print(f"  ✓ {field:25s} | Coverage: {coverage:5.1f}% | Uniqueness: {uniqueness:5.1f}% | Avg Length: {avg_length:5.1f}")
            print(f"    Reason: {reason}")
    
    print(f"\n🟠 2.0x (Important): {len(weights['2.0x'])} fields")
    for field in weights['2.0x']:
        field_analysis = next((r for r in analysis['results'] if r['column'] == field), None)
        if field_analysis:
            reason = field_analysis.get('name_reason', 'N/A')
            coverage = field_analysis.get('data_analysis', {}).get('coverage', 0) * 100
            print(f"  ✓ {field:25s} | Coverage: {coverage:5.1f}% | {reason[:50]}")
    
    print(f"\n🟡 1.0x (Supporting): {len(weights['1.0x'])} fields")
    for field in weights['1.0x'][:10]:  # Show first 10
        field_analysis = next((r for r in analysis['results'] if r['column'] == field), None)
        if field_analysis:
            reason = field_analysis.get('name_reason', 'N/A')
            print(f"  • {field:25s} | {reason[:50]}")
    if len(weights['1.0x']) > 10:
        print(f"  ... and {len(weights['1.0x']) - 10} more")
    
    print(f"\n⚪ 0.5x (Low Priority): {len(weights['0.5x'])} fields")
    for field in weights['0.5x']:
        field_analysis = next((r for r in analysis['results'] if r['column'] == field), None)
        if field_analysis:
            reason = field_analysis.get('name_reason', 'N/A')
            print(f"  • {field:25s} | {reason[:50]}")
    
    print(f"\n❌ Excluded: {len(weights['exclude'])} fields")
    for field in weights['exclude']:
        field_analysis = next((r for r in analysis['results'] if r['column'] == field), None)
        if field_analysis:
            reason = field_analysis.get('name_reason', 'N/A')
            print(f"  ✗ {field:25s} | {reason[:50]}")
    
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS (Top 10 Fields)")
    print("=" * 80)
    
    for i, field_result in enumerate(analysis['results'][:10], 1):
        if field_result['final_weight'] > 0:
            print(f"\n{i}. {field_result['column']} ({field_result['type']})")
            print(f"   Final Weight: {field_result['final_weight']}x")
            print(f"   Name Weight: {field_result['name_weight']}x")
            print(f"   Reason: {field_result['name_reason']}")
            if field_result['data_analysis']:
                da = field_result['data_analysis']
                print(f"   Data Quality:")
                print(f"     - Coverage: {da['coverage']*100:.1f}%")
                print(f"     - Uniqueness: {da['uniqueness']*100:.1f}%")
                print(f"     - Diversity: {da['diversity']*100:.1f}%")
                print(f"     - Avg Length: {da['avg_length']:.1f} chars")
                print(f"     - Score: {da['score']:.3f}")


def main():
    """Main function."""
    print("=" * 80)
    print("TESTING INTELLIGENT FIELD ANALYSIS WITH EXAMPLE TABLE")
    print("=" * 80)
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5433")),
            database=os.getenv("POSTGRES_DATABASE", "ai_requests_db"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        
        cursor = conn.cursor()
        
        # Create test table
        create_test_table(cursor)
        conn.commit()
        
        # Run analysis
        run_analysis(cursor)
        
        # Cleanup (optional - comment out if you want to keep the table)
        print("\n" + "=" * 80)
        print("CLEANUP")
        print("=" * 80)
        # Auto-drop for testing (change to False to keep table)
        auto_drop = True
        if auto_drop:
            cursor.execute("DROP TABLE IF EXISTS test_requests CASCADE;")
            conn.commit()
            print("✓ Test table dropped")
        else:
            print("✓ Test table kept (you can query it manually)")
        
        cursor.close()
        conn.close()
        
        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

