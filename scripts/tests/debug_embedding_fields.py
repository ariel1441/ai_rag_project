"""
Debug script to check what fields are being found and used in embeddings.
"""
import os
import psycopg2
from dotenv import load_dotenv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.text_processing import combine_text_fields_weighted, chunk_text

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=int(os.getenv('POSTGRES_PORT', 5433)),
    database=os.getenv('POSTGRES_DATABASE', 'ai_requests_db'),
    user=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD', 'password'),
)

cursor = conn.cursor()
cursor.execute("SELECT * FROM requests LIMIT 5;")

columns = [desc[0] for desc in cursor.description]
requests = [dict(zip(columns, row)) for row in cursor.fetchall()]

print("=" * 80)
print("FIELD MATCHING DEBUG")
print("=" * 80)
print()

# Check first request
if requests:
    req = requests[0]
    print(f"Request ID: {req.get('requestid') or req.get('\\ufeffrequestid', 'NOT FOUND')}")
    print()
    
    print("Available columns in database:")
    print(f"  Total: {len(columns)} columns")
    print(f"  First 10: {columns[:10]}")
    print()
    
    # Test field matching
    print("Testing field matching:")
    test_fields = [
        'projectname', 'updatedby', 'requesttypeid', 'requeststatusid',
        'responsibleemployeename', 'areadesc', 'projectdesc', 'remarks',
        'contactfirstname', 'contactlastname', 'createddate', 'updatedate'
    ]
    
    found_count = 0
    for field in test_fields:
        # Try different variations
        value = None
        for col in columns:
            clean_col = col.lstrip('\ufeff').strip().lower()
            if clean_col == field.lower():
                value = req[col]
                break
        
        if value and str(value).strip() and str(value).upper() not in ('NULL', 'NONE', ''):
            found_count += 1
            print(f"  ✓ {field}: Found (value: {str(value)[:50]}...)")
        else:
            print(f"  ✗ {field}: NOT FOUND or empty")
    
    print()
    print(f"Found {found_count}/{len(test_fields)} test fields")
    print()
    
    # Test combine_text_fields_weighted
    print("Testing combine_text_fields_weighted:")
    combined = combine_text_fields_weighted(req)
    print(f"  Combined text length: {len(combined)} characters")
    print(f"  Combined text preview: {combined[:200]}...")
    print()
    
    # Test chunking
    chunks = chunk_text(combined, max_chunk_size=512, overlap=50)
    print(f"  Number of chunks: {len(chunks)}")
    print(f"  Chunk sizes: {[len(c) for c in chunks[:5]]}")
    print()
    
    # Check what fields are actually in the combined text
    field_labels_in_text = []
    for label in ['Project:', 'Updated By:', 'Type:', 'Status:', 'Area:', 'Description:', 'Remarks:']:
        if label in combined:
            field_labels_in_text.append(label)
    
    print(f"  Fields found in combined text: {len(field_labels_in_text)}")
    print(f"  Field labels: {field_labels_in_text}")
    print()

# Check all requests
print("=" * 80)
print("STATISTICS FOR ALL REQUESTS")
print("=" * 80)
print()

cursor.execute("SELECT COUNT(*) FROM requests;")
total_requests = cursor.fetchone()[0]

total_chunks = 0
total_chars = 0
sample_sizes = []

for i, req in enumerate(requests[:100]):  # Sample first 100
    combined = combine_text_fields_weighted(req)
    chunks = chunk_text(combined, max_chunk_size=512, overlap=50)
    total_chunks += len(chunks)
    total_chars += len(combined)
    sample_sizes.append(len(chunks))

if requests:
    avg_chunks = total_chunks / len(requests)
    avg_chars = total_chars / len(requests)
    
    print(f"Sample: {len(requests)} requests")
    print(f"Average chunks per request: {avg_chunks:.2f}")
    print(f"Average text length: {avg_chars:.0f} characters")
    print(f"Chunk size range: {min(sample_sizes)} - {max(sample_sizes)}")
    print()
    print(f"Projected total chunks for {total_requests} requests:")
    print(f"  {avg_chunks * total_requests:.0f} chunks")
    print()
    print(f"Your current: 26,000 chunks")
    print(f"Expected: ~{avg_chunks * total_requests:.0f} chunks")
    print(f"Previous: 40,000 chunks")
    print()

cursor.close()
conn.close()

