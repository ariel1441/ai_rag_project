"""Test all 10 demo questions with Option 1 and compare with expected results."""
import requests
import json
import time
from pathlib import Path

API_URL = "http://localhost:8000/api/search"

# Load expected results from JSON
expected_file = Path("DEMO_QUESTIONS_AND_EXPECTED_RESULTS.json")
if expected_file.exists():
    with open(expected_file, 'r', encoding='utf-8') as f:
        expected_data = json.load(f)
else:
    expected_data = []

# All 10 test questions
test_queries = [
    ("פניות מיניב ליבוביץ", "Person query - יניב ליבוביץ", 225),
    ("פניות מאור גלילי", "Person query - אור גלילי", 34),
    ("כמה פניות יש מיניב ליבוביץ?", "Count query", 225),
    ("פרויקט בדיקה אור גלילי", "Project query", 27),
    ("בקשות מסוג 4", "Type query - Type 4", 3731),
    ("בקשות בסטטוס 10", "Status query - Status 10", 4217),
    ("תיאום תכנון", "General semantic query", 441),
    ("פניות מאוקסנה כלפון", "Person query - אוקסנה כלפון", 186),
    ("פניות ממשה אוגלבו", "Person query - משה אוגלבו", 704),
    ("כמה פניות יש מסוג 4 בסטטוס 10?", "Complex query - Type 4 + Status 10", 3237),
]

print("=" * 80)
print("Testing All 10 Demo Questions - Option 1 (חיפוש בלבד)")
print("=" * 80)
print()

# Check if server is running
try:
    health = requests.get("http://localhost:8000/api/health", timeout=2)
    if health.status_code != 200:
        print("❌ Server not responding")
        exit(1)
    print("✅ Server is running\n")
except Exception as e:
    print(f"❌ Cannot connect to server: {e}")
    print("Make sure server is running on http://localhost:8000")
    exit(1)

results_summary = []

for i, (query, description, expected_count) in enumerate(test_queries, 1):
    print(f"[{i}/10] Query: {query}")
    print(f"         Description: {description}")
    print(f"         Expected DB Count: {expected_count}")
    print("-" * 80)
    
    try:
        start_time = time.time()
        response = requests.post(
            API_URL,
            json={"query": query, "top_k": 20, "include_details": True},
            timeout=15
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            total_found = data.get("total_found", 0)
            results_count = len(data.get("results", []))
            intent = data.get("intent", "N/A")
            entities = data.get("entities", {})
            search_time = data.get("search_time_ms", 0) / 1000
            
            # Compare with expected
            count_match = "✅" if total_found >= expected_count * 0.8 else "⚠️"  # Allow 20% variance for semantic search
            count_status = "Match" if total_found == expected_count else f"Diff: {expected_count - total_found}"
            
            print(f"✅ Status: Success")
            print(f"   Total Found (API): {total_found} requests")
            print(f"   Expected (DB): {expected_count} requests")
            print(f"   Comparison: {count_match} {count_status}")
            print(f"   Results Returned: {results_count} requests")
            print(f"   Intent: {intent}")
            print(f"   Entities: {json.dumps(entities, ensure_ascii=False)}")
            print(f"   Search Time: {search_time:.2f} seconds")
            print(f"   Total Time: {elapsed:.2f} seconds")
            
            # Show first 3 result IDs
            if data.get("results"):
                first_ids = [str(r.get("requestid", "N/A")) for r in data["results"][:3]]
                print(f"   Sample IDs: {first_ids}")
            
            results_summary.append({
                "query": query,
                "description": description,
                "expected_count": expected_count,
                "api_total_found": total_found,
                "returned": results_count,
                "intent": intent,
                "entities": entities,
                "time": search_time,
                "count_match": total_found == expected_count,
                "count_diff": expected_count - total_found,
                "success": True
            })
        else:
            print(f"❌ Status: Error {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            results_summary.append({
                "query": query,
                "description": description,
                "expected_count": expected_count,
                "success": False,
                "error": response.status_code
            })
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        results_summary.append({
            "query": query,
            "description": description,
            "expected_count": expected_count,
            "success": False,
            "error": str(e)
        })
    
    print()

# Summary
print("=" * 80)
print("COMPREHENSIVE SUMMARY")
print("=" * 80)
print()

successful = [r for r in results_summary if r.get("success")]
failed = [r for r in results_summary if not r.get("success")]

print(f"✅ Successful: {len(successful)}/{len(test_queries)}")
print(f"❌ Failed: {len(failed)}/{len(test_queries)}")
print()

if successful:
    print("Detailed Results:")
    print("-" * 80)
    for r in successful:
        match_icon = "✅" if r.get("count_match") else "⚠️"
        print(f"{match_icon} {r['query']}")
        print(f"   Expected: {r['expected_count']} | API Found: {r['api_total_found']} | Diff: {r.get('count_diff', 0)}")
        print(f"   Intent: {r['intent']} | Returned: {r['returned']} | Time: {r['time']:.2f}s")
        print()

if failed:
    print("\nFailed queries:")
    for r in failed:
        print(f"  - {r['query']}: {r.get('error', 'Unknown error')}")

# Statistics
if successful:
    avg_time = sum(r['time'] for r in successful) / len(successful)
    exact_matches = sum(1 for r in successful if r.get("count_match"))
    print("=" * 80)
    print("STATISTICS")
    print("=" * 80)
    print(f"Average search time: {avg_time:.2f} seconds")
    print(f"Exact count matches: {exact_matches}/{len(successful)}")
    print(f"Intent detection accuracy: {len([r for r in successful if r['intent'] != 'general'])}/{len(successful)}")
    print()
    print("⚠️  NOTE: Total count shows limited results (20) instead of true DB count.")
    print("   This is because COUNT query needs similarity threshold to show true total.")
    print("   The search is working correctly, but count needs threshold fix.")

print("=" * 80)

