"""
Diagnose why embedding generation is producing fewer chunks than expected.
This script uses the same connection and logic as generate_embeddings.py
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.utils.text_processing import combine_text_fields_weighted, chunk_text

load_dotenv()

print("=" * 80)
print("EMBEDDING GENERATION DIAGNOSTIC")
print("=" * 80)
print()

# Connect to database (same as generate_embeddings.py)
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=int(os.getenv('POSTGRES_PORT', 5433)),
    database=os.getenv('POSTGRES_DATABASE', 'ai_requests_db'),
    user=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD', 'password'),
)

cursor = conn.cursor()

# Get total count
cursor.execute("SELECT COUNT(*) FROM requests;")
total_requests = cursor.fetchone()[0]
print(f"Total requests in database: {total_requests:,}")
print()

# Get sample of requests
cursor.execute("SELECT * FROM requests LIMIT 10;")
columns = [desc[0] for desc in cursor.description]
requests = [dict(zip(columns, row)) for row in cursor.fetchall()]

print(f"Columns in database: {len(columns)}")
print(f"First 20 columns: {columns[:20]}")
print()

# Test field matching for all fields in combine_text_fields_weighted
print("=" * 80)
print("FIELD MATCHING TEST")
print("=" * 80)
print()

# All fields that should be in combine_text_fields_weighted
expected_fields = {
    # Weight 3.0x
    'projectname', 'updatedby', 'requesttypeid', 'requeststatusid',
    'responsibleemployeename', 'requeststatusdate', 'requestsourcenun',
    'createdby', 'areadesc', 'projectdesc', 'remarks',
    # Weight 2.0x
    'createddate', 'updatedate', 'requesttypereasonid', 'contactfirstname',
    'contactlastname', 'contactemail', 'yazam_contactname', 'yazam_contactemail',
    'yazam_companyname',
    # Weight 1.0x
    'responsibleorgentityname', 'responsibleemployeerolename',
    'penetrategrounddesc', 'requestjobshortdescription', 'externalrequeststatusdesc',
    'penetrategroundtypeid', 'contactphone', 'yazam_contactphone', 'requestcontacttz',
    'plannum',
    # Weight 0.5x (booleans)
    'ispenetrateground', 'isactive', 'isconvert', 'ismanual', 'ismekorotlayer',
    'isareafilevalid', 'ismekorottama1layer', 'isimportentproject', 'isnewdocuments',
    # Weight 0.5x (coordinates)
    'areacenterx', 'areacentery', 'extentminx', 'extentminy', 'extentmaxx',
    'extentmaxy', 'areainsquare'
}

# Check which fields exist in database
db_columns_lower = {col.lstrip('\ufeff').strip().lower(): col for col in columns}

found_fields = {}
missing_fields = []

for field in expected_fields:
    field_lower = field.lower()
    if field_lower in db_columns_lower:
        found_fields[field] = db_columns_lower[field_lower]
    else:
        missing_fields.append(field)

print(f"Expected fields: {len(expected_fields)}")
print(f"Found in database: {len(found_fields)}")
print(f"Missing from database: {len(missing_fields)}")
print()

if missing_fields:
    print("Missing fields:")
    for field in missing_fields[:20]:  # Show first 20
        print(f"  ✗ {field}")
    if len(missing_fields) > 20:
        print(f"  ... and {len(missing_fields) - 20} more")
    print()

# Test actual field retrieval on sample requests
print("=" * 80)
print("ACTUAL FIELD RETRIEVAL TEST (Sample Requests)")
print("=" * 80)
print()

total_chunks = 0
total_text_length = 0
field_usage_count = {field: 0 for field in expected_fields}

for i, req in enumerate(requests):
    combined = combine_text_fields_weighted(req)
    chunks = chunk_text(combined, max_chunk_size=512, overlap=50)
    
    total_chunks += len(chunks)
    total_text_length += len(combined)
    
    # Count which fields appear in combined text
    for field in expected_fields:
        if field in found_fields:
            db_col = found_fields[field]
            value = req.get(db_col)
            if value and str(value).strip() and str(value).upper() not in ('NULL', 'NONE', ''):
                field_usage_count[field] += 1

if requests:
    avg_chunks = total_chunks / len(requests)
    avg_text_length = total_text_length / len(requests)
    
    print(f"Sample size: {len(requests)} requests")
    print(f"Average chunks per request: {avg_chunks:.2f}")
    print(f"Average text length: {avg_text_length:.0f} characters")
    print()
    
    # Show field usage
    used_fields = {k: v for k, v in field_usage_count.items() if v > 0}
    unused_fields = {k: v for k, v in field_usage_count.items() if v == 0}
    
    print(f"Fields actually used (have data): {len(used_fields)}")
    print(f"Fields never used (empty/null): {len(unused_fields)}")
    print()
    
    print("Top 10 most used fields:")
    sorted_used = sorted(used_fields.items(), key=lambda x: x[1], reverse=True)
    for field, count in sorted_used[:10]:
        print(f"  {field}: {count}/{len(requests)} requests ({count*100//len(requests)}%)")
    print()
    
    if unused_fields:
        print("Fields never used (might be missing from DB or always empty):")
        for field in list(unused_fields.keys())[:15]:
            print(f"  ✗ {field}")
        if len(unused_fields) > 15:
            print(f"  ... and {len(unused_fields) - 15} more")
        print()
    
    # Project total
    projected_chunks = avg_chunks * total_requests
    print("=" * 80)
    print("PROJECTION")
    print("=" * 80)
    print(f"Projected total chunks for {total_requests:,} requests: {projected_chunks:,.0f}")
    print(f"Your current result: 26,000 chunks")
    print(f"Previous result: 40,000 chunks")
    print()
    
    if projected_chunks < 30000:
        print("⚠️  WARNING: Projected chunks are much lower than expected!")
        print("   This suggests many fields are not being found or are empty.")
        print()
        print("Possible causes:")
        print("  1. CSV import had fewer columns than original database")
        print("  2. Field names don't match (case/BOM issues)")
        print("  3. Many fields are NULL/empty in the imported data")
        print("  4. get_value() function is not finding fields correctly")
    elif projected_chunks > 35000:
        print("✓ Projected chunks look reasonable!")
        print("   If actual result is 26,000, there might be an issue with:")
        print("  1. Some requests being skipped")
        print("  2. Chunking logic being too aggressive")
        print("  3. Empty combined text for some requests")

cursor.close()
conn.close()

print()
print("=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)

