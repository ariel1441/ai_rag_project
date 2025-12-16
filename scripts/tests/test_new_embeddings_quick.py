"""
Quick test of new embedding function with 1-2 sample requests.
This verifies the new combine_text_fields_weighted() works before regenerating all embeddings.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import psycopg2
from sentence_transformers import SentenceTransformer
from utils.text_processing import combine_text_fields_weighted
from utils.database import get_db_connection

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

print("=" * 80)
print("QUICK TEST: New Embedding Function")
print("=" * 80)
print()

# Get 2 sample requests
print("Step 1: Loading 2 sample requests from database...")
conn = get_db_connection(register_pgvector=False)
cursor = conn.cursor()

cursor.execute("""
    SELECT * FROM requests
    ORDER BY requestid
    LIMIT 2;
""")

columns = [desc[0] for desc in cursor.description]
requests = [dict(zip(columns, row)) for row in cursor.fetchall()]

print(f"✓ Loaded {len(requests)} requests")
print()

# Test the new function
print("Step 2: Testing combine_text_fields_weighted()...")
print()

for i, req in enumerate(requests, 1):
    request_id = req.get('requestid')
    print(f"Request {i}: ID = {request_id}")
    print("-" * 80)
    
    # Test new function
    combined_text = combine_text_fields_weighted(req)
    
    print(f"Combined text length: {len(combined_text)} characters")
    print()
    print("First 500 characters:")
    print(combined_text[:500])
    if len(combined_text) > 500:
        print("...")
    print()
    
    # Count fields
    field_count = combined_text.count(": ")
    print(f"Fields included: ~{field_count}")
    print()
    
    # Check for key fields
    key_fields = ['Updated By', 'Created By', 'Responsible Employee', 'Contact First Name', 'Type']
    found_fields = [field for field in key_fields if field in combined_text]
    print(f"Key fields found: {', '.join(found_fields)}")
    print()

print("=" * 80)
print("Step 3: Generating embeddings for test requests...")
print()

# Load model
print("Loading embedding model...")
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
print("✓ Model loaded")
print()

# Generate embeddings
test_texts = []
for req in requests:
    combined_text = combine_text_fields_weighted(req)
    if combined_text:
        test_texts.append(combined_text)

if test_texts:
    print(f"Generating embeddings for {len(test_texts)} text(s)...")
    embeddings = model.encode(
        test_texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    print(f"✓ Generated {len(embeddings)} embeddings")
    print(f"  Embedding dimensions: {embeddings[0].shape[0]}")
    print()
    
    print("=" * 80)
    print("✅ SUCCESS! New embedding function works!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Tested {len(requests)} requests")
    print(f"  - Combined text length: {len(test_texts[0])} characters (first request)")
    print(f"  - Embeddings generated: {len(embeddings)}")
    print(f"  - Embedding dimensions: {embeddings[0].shape[0]}")
    print()
    print("Next steps:")
    print("  1. If this looks good, you can regenerate all embeddings")
    print("  2. Run: python scripts/core/generate_embeddings.py")
    print("  3. This will take 1-3 hours for all requests")
    print()
else:
    print("⚠️ No text generated - check the function!")

conn.close()

print("=" * 80)

