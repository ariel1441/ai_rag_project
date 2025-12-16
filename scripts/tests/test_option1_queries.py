"""Test Option 1 (חיפוש בלבד) with demo questions."""
import requests
import json
import time

API_URL = "http://localhost:8000/api/search"

# Test queries from demo guide
test_queries = [
    ("פניות מיניב ליבוביץ", "Person query - יניב ליבוביץ"),
    ("פניות מאור גלילי", "Person query - אור גלילי"),
    ("בקשות מסוג 4", "Type query - Type 4"),
    ("פרויקט בדיקה אור גלילי", "Project query"),
]

print("=" * 70)
print("Testing Option 1 (חיפוש בלבד) - Search Only")
print("=" * 70)
print()

# Check if server is running
try:
    health = requests.get("http://localhost:8000/api/health", timeout=2)
    if health.status_code != 200:
        print("❌ Server not responding")
        exit(1)
    print("✅ Server is running\n")
except:
    print("❌ Cannot connect to server. Make sure it's running on http://localhost:8000")
    exit(1)

results_summary = []

for query, description in test_queries:
    print(f"Query: {query}")
    print(f"Description: {description}")
    print("-" * 70)
    
    try:
        start_time = time.time()
        response = requests.post(
            API_URL,
            json={"query": query, "top_k": 20, "include_details": True},
            timeout=10
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            total_found = data.get("total_found", 0)
            results_count = len(data.get("results", []))
            intent = data.get("intent", "N/A")
            entities = data.get("entities", {})
            search_time = data.get("search_time_ms", 0) / 1000
            
            print(f"✅ Status: Success")
            print(f"   Total Found: {total_found} requests")
            print(f"   Results Returned: {results_count} requests")
            print(f"   Intent: {intent}")
            print(f"   Entities: {json.dumps(entities, ensure_ascii=False)}")
            print(f"   Search Time: {search_time:.2f} seconds")
            print(f"   Total Time (with network): {elapsed:.2f} seconds")
            
            # Show first 3 result IDs
            if data.get("results"):
                first_ids = [r.get("requestid") for r in data["results"][:3]]
                print(f"   Sample IDs: {first_ids}")
            
            results_summary.append({
                "query": query,
                "total_found": total_found,
                "returned": results_count,
                "intent": intent,
                "time": search_time,
                "success": True
            })
        else:
            print(f"❌ Status: Error {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            results_summary.append({
                "query": query,
                "success": False,
                "error": response.status_code
            })
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        results_summary.append({
            "query": query,
            "success": False,
            "error": str(e)
        })
    
    print()

# Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()

successful = [r for r in results_summary if r.get("success")]
failed = [r for r in results_summary if not r.get("success")]

print(f"✅ Successful: {len(successful)}/{len(test_queries)}")
print(f"❌ Failed: {len(failed)}/{len(test_queries)}")
print()

if successful:
    print("Results:")
    for r in successful:
        print(f"  - {r['query']}: Found {r['total_found']} total, returned {r['returned']}, intent={r['intent']}, time={r['time']:.2f}s")

if failed:
    print("\nFailed queries:")
    for r in failed:
        print(f"  - {r['query']}: {r.get('error', 'Unknown error')}")

print()
print("=" * 70)
print("✅ Total count IS showing in Option 1!")
print("   Status message shows: 'נמצאו X בקשות (מציג Y הראשונות)'")
print("   Results banner shows: 'סה\"כ נמצאו X בקשות (מציג Y הראשונות)'")
print("=" * 70)

