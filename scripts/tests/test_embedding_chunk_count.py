"""
Test script to verify embedding chunk generation on existing project.
This counts chunks WITHOUT modifying the database - just tests the logic.
"""
import os
import sys
from pathlib import Path
import psycopg2
from tqdm import tqdm

# Try to load dotenv (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.utils.text_processing import combine_text_fields_weighted, chunk_text

print("=" * 80)
print("TESTING EMBEDDING CHUNK GENERATION (READ-ONLY)")
print("=" * 80)
print()
print("This will test the current logic on your existing database")
print("to verify it still produces ~40,000 chunks (not 26,000)")
print()

# Connect to database
print("Connecting to database...")
print("  (Trying port 5432 first for existing project, then 5433 for new PC)")
print()

# Try both ports (existing project usually 5432, new PC Docker is 5433)
ports_to_try = [
    int(os.getenv('POSTGRES_PORT', 5432)),  # Existing project default
    5433,  # New PC Docker default
]

conn = None
for port in ports_to_try:
    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=port,
            database=os.getenv('POSTGRES_DATABASE', 'ai_requests_db'),
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', 'password'),
        )
        print(f"✓ Connected to port {port}")
        break
    except psycopg2.OperationalError as e:
        if port == ports_to_try[-1]:  # Last port failed
            print(f"❌ ERROR: Could not connect to database on any port")
            print(f"   Tried ports: {ports_to_try}")
            print(f"   Error: {e}")
            sys.exit(1)
        continue

if not conn:
    print("❌ ERROR: Could not establish database connection")
    sys.exit(1)

print()

cursor = conn.cursor()

# Get total count
cursor.execute("SELECT COUNT(*) FROM requests;")
total_requests = cursor.fetchone()[0]
print(f"Total requests in database: {total_requests:,}")
print()

# Get all requests (same as generate_embeddings.py)
print("Loading all requests...")
cursor.execute("SELECT * FROM requests;")
columns = [desc[0] for desc in cursor.description]
all_rows = cursor.fetchall()
requests = [dict(zip(columns, row)) for row in all_rows]
print(f"✓ Loaded {len(requests):,} requests")
print()

# Find ID column (same logic as generate_embeddings.py)
id_col_original = None
for col in columns:
    clean_col = col.lstrip('\ufeff').strip()
    if clean_col.lower() == 'requestid':
        id_col_original = col
        break

if not id_col_original:
    print("❌ ERROR: Could not find requestid column!")
    cursor.close()
    conn.close()
    sys.exit(1)

print(f"Using ID column: '{id_col_original}'")
print()

# Test chunk generation (same logic as generate_embeddings.py)
print("=" * 80)
print("GENERATING CHUNKS (TEST MODE - NOT SAVING)")
print("=" * 80)
print()

total_chunks = 0
skipped_requests = 0
empty_text_requests = 0
chunk_counts = []
text_lengths = []

# Sample first 5 for detailed analysis
sample_requests = []

for i, req in enumerate(tqdm(requests, desc="Processing requests")):
    # Get request ID
    request_id = str(req[id_col_original]) if req.get(id_col_original) else None
    
    if not request_id:
        skipped_requests += 1
        continue
    
    # Combine text fields using weighted version
    combined_text = combine_text_fields_weighted(req)
    
    # Skip if text is empty
    if not combined_text or not combined_text.strip():
        empty_text_requests += 1
        continue
    
    # Chunk if necessary (same parameters as generate_embeddings.py)
    chunks = chunk_text(combined_text, max_chunk_size=512, overlap=50)
    
    total_chunks += len(chunks)
    chunk_counts.append(len(chunks))
    text_lengths.append(len(combined_text))
    
    # Save first 5 for detailed analysis
    if len(sample_requests) < 5:
        sample_requests.append({
            'id': request_id,
            'text_length': len(combined_text),
            'chunks': len(chunks),
            'text_preview': combined_text[:200]
        })

print()
print("=" * 80)
print("RESULTS")
print("=" * 80)
print()

print(f"Total requests processed: {len(requests):,}")
print(f"  - Skipped (no ID): {skipped_requests}")
print(f"  - Skipped (empty text): {empty_text_requests}")
print(f"  - Successfully processed: {len(requests) - skipped_requests - empty_text_requests:,}")
print()

if chunk_counts:
    avg_chunks = sum(chunk_counts) / len(chunk_counts)
    min_chunks = min(chunk_counts)
    max_chunks = max(chunk_counts)
    median_chunks = sorted(chunk_counts)[len(chunk_counts) // 2]
    
    avg_text_length = sum(text_lengths) / len(text_lengths)
    min_text_length = min(text_lengths)
    max_text_length = max(text_lengths)
    
    print(f"TOTAL CHUNKS GENERATED: {total_chunks:,}")
    print()
    print(f"Chunks per request:")
    print(f"  - Average: {avg_chunks:.2f}")
    print(f"  - Median: {median_chunks}")
    print(f"  - Min: {min_chunks}")
    print(f"  - Max: {max_chunks}")
    print()
    print(f"Text length per request:")
    print(f"  - Average: {avg_text_length:.0f} chars")
    print(f"  - Min: {min_text_length} chars")
    print(f"  - Max: {max_text_length:,} chars")
    print()
    
    # Comparison
    print("=" * 80)
    print("COMPARISON")
    print("=" * 80)
    print()
    print(f"Current test result: {total_chunks:,} chunks")
    print(f"Expected (previous): ~40,000 chunks")
    print(f"New PC result: ~26,000 chunks")
    print()
    
    if total_chunks >= 35000:
        print("✓ GOOD: Chunk count is close to expected (~40,000)")
        print("  The logic is working correctly on the existing database.")
        print("  The issue is likely with the CSV import data (fewer fields/missing data).")
    elif total_chunks >= 25000:
        print("⚠️  WARNING: Chunk count is lower than expected")
        print("  This suggests the logic might have been affected.")
        print("  Need to investigate further.")
    else:
        print("❌ ERROR: Chunk count is much lower than expected!")
        print("  The logic has been broken. Need to fix immediately.")
    
    print()
    print("=" * 80)
    print("SAMPLE REQUESTS (First 5)")
    print("=" * 80)
    print()
    for i, sample in enumerate(sample_requests, 1):
        print(f"Sample {i}:")
        print(f"  ID: {sample['id']}")
        print(f"  Text length: {sample['text_length']} chars")
        print(f"  Chunks: {sample['chunks']}")
        print(f"  Preview: {sample['text_preview']}...")
        print()

cursor.close()
conn.close()

print("=" * 80)
print("TEST COMPLETE")
print("=" * 80)

