"""
Analyze all fields in the requests table to determine which should be included in embeddings
and what weights they should have.
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

print("=" * 80)
print("ANALYZE ALL FIELDS FOR EMBEDDING WEIGHTING")
print("=" * 80)
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
    
    # Get all columns
    print("Step 1: Getting all columns from requests table...")
    print()
    
    cursor.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns
        WHERE table_name = 'requests'
        ORDER BY ordinal_position;
    """)
    
    columns = cursor.fetchall()
    print(f"Found {len(columns)} columns total")
    print()
    
    # Analyze each field
    print("=" * 80)
    print("FIELD ANALYSIS")
    print("=" * 80)
    print()
    
    # Categories
    critical_fields = []
    important_fields = []
    supporting_fields = []
    low_priority_fields = []
    exclude_fields = []
    
    # Field patterns to categorize
    for col_name, data_type, max_length in columns:
        col_lower = col_name.lower()
        
        # Check if field has data
        try:
            cursor.execute(f"""
                SELECT 
                    COUNT(*) as total,
                    COUNT({col_name}) as non_null,
                    COUNT(DISTINCT {col_name}) as distinct_values
                FROM requests;
            """)
            stats = cursor.fetchone()
            total, non_null, distinct = stats
            
            # Sample values
            cursor.execute(f"""
                SELECT {col_name}
                FROM requests
                WHERE {col_name} IS NOT NULL
                  AND {col_name}::text != ''
                LIMIT 3;
            """)
            samples = [row[0] for row in cursor.fetchall()]
            
            # Categorize based on name and content
            category = None
            weight = None
            reason = ""
            
            # CRITICAL: Core descriptive text fields
            if any(x in col_lower for x in ['projectname', 'projectdesc', 'areadesc', 'remarks', 
                                            'description', 'job', 'penetrategrounddesc']):
                category = "CRITICAL"
                weight = 3.0
                reason = "Core descriptive text - main content of request"
                critical_fields.append((col_name, weight, reason, non_null, distinct, samples))
            
            # IMPORTANT: Names, contacts, responsible people, status/type
            elif any(x in col_lower for x in ['name', 'contact', 'responsible', 'employee', 
                                               'updatedby', 'createdby', 'status', 'type']):
                category = "IMPORTANT"
                weight = 2.0
                reason = "Names, contacts, responsible people, or status/type info"
                important_fields.append((col_name, weight, reason, non_null, distinct, samples))
            
            # SUPPORTING: IDs, numbers, dates, metadata
            elif any(x in col_lower for x in ['id', 'num', 'number', 'date', 'org', 'company', 
                                               'authority', 'source', 'reference', 'plan']):
                category = "SUPPORTING"
                weight = 1.0
                reason = "IDs, numbers, dates, or metadata"
                supporting_fields.append((col_name, weight, reason, non_null, distinct, samples))
            
            # LOW PRIORITY: Coordinates, flags, technical
            elif any(x in col_lower for x in ['x', 'y', 'min', 'max', 'extent', 'center', 
                                               'is', 'flag', 'convert', 'manual', 'active', 
                                               'valid', 'square', 'tz']):
                category = "LOW_PRIORITY"
                weight = 0.5
                reason = "Coordinates, flags, or technical fields"
                low_priority_fields.append((col_name, weight, reason, non_null, distinct, samples))
            
            # EXCLUDE: Internal IDs, timestamps (unless needed)
            elif any(x in col_lower for x in ['requestid', 'externaluserid', 'usercompanyroleid',
                                               'receptiondate', 'responsedate', 'publicationdate',
                                               'sladate', 'createddate', 'updatedate']):
                category = "EXCLUDE"
                weight = 0.0
                reason = "Internal IDs or timestamps (not useful for semantic search)"
                exclude_fields.append((col_name, weight, reason, non_null, distinct, samples))
            
            else:
                # Unknown - default to supporting
                category = "SUPPORTING"
                weight = 1.0
                reason = "Unknown category - default to supporting"
                supporting_fields.append((col_name, weight, reason, non_null, distinct, samples))
        
        except Exception as e:
            # Field might have issues, skip
            exclude_fields.append((col_name, 0.0, f"Error analyzing: {str(e)[:50]}", 0, 0, []))
            continue
    
    # Print results
    def print_category(title, fields_list, color="✓"):
        if not fields_list:
            return
        print(f"\n{title} (Weight: {fields_list[0][1] if fields_list else 'N/A'}x)")
        print("-" * 80)
        for col_name, weight, reason, non_null, distinct, samples in fields_list:
            pct = (non_null / len(columns) * 100) if columns else 0
            print(f"  {color} {col_name:40s} | {non_null:5d} non-null ({pct:.1f}%) | {distinct:5d} distinct")
            print(f"    Reason: {reason}")
            if samples:
                sample_str = ", ".join([str(s)[:30] for s in samples[:2]])
                print(f"    Samples: {sample_str}")
            print()
    
    print_category("🔴 CRITICAL FIELDS", critical_fields, "🔴")
    print_category("🟠 IMPORTANT FIELDS", important_fields, "🟠")
    print_category("🟡 SUPPORTING FIELDS", supporting_fields, "🟡")
    print_category("⚪ LOW PRIORITY FIELDS", low_priority_fields, "⚪")
    print_category("❌ EXCLUDE FIELDS", exclude_fields, "❌")
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Total fields: {len(columns)}")
    print(f"  🔴 Critical: {len(critical_fields)}")
    print(f"  🟠 Important: {len(important_fields)}")
    print(f"  🟡 Supporting: {len(supporting_fields)}")
    print(f"  ⚪ Low Priority: {len(low_priority_fields)}")
    print(f"  ❌ Exclude: {len(exclude_fields)}")
    print()
    print("RECOMMENDATION:")
    print("  - Include: Critical + Important + Supporting (maybe Low Priority)")
    print("  - Exclude: Internal IDs, timestamps, coordinates (unless needed)")
    print()
    
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)

