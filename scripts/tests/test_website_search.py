"""Test search on website after threshold fix."""
import requests
import json
import time

API_URL = "http://localhost:8000/api/search"

test_queries = [
    ("פניות מיניב ליבוביץ", 225),
    ("פניות מאור גלילי", 34),
    ("בקשות מסוג 4", 3731),
    ("פרויקט בדיקה אור גלילי", 27),
]

print("=" * 70)
print("Testing Website Search with Threshold Fix")
print("=" * 70)
print()

# Wait for server
for i in range(10):
    try:
        health = requests.get("http://localhost:8000/api/health", timeout=2)
        if health.status_code == 200:
            print("✅ Server is running\n")
            break
    except:
        if i < 9:
            print(f"Waiting for server... ({i+1}/10)")
            time.sleep(1)
        else:
            print("❌ Server not responding")
            exit(1)

for query, expected in test_queries:
    try:
        response = requests.post(
            API_URL,
            json={"query": query, "top_k": 20, "include_details": True},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            total = data.get("total_found", 0)
            returned = len(data.get("results", []))
            
            diff = abs(total - expected)
            match = "✅" if diff < expected * 0.3 else "⚠️"  # Within 30% is good
            
            print(f"{match} {query}")
            print(f"   Expected: {expected} | Got: {total} | Returned: {returned}")
            print()
        else:
            print(f"❌ {query}: Error {response.status_code}")
            print()
    except Exception as e:
        print(f"❌ {query}: {str(e)}")
        print()

print("=" * 70)
print("✅ Test complete! Check the website at http://localhost:8000")
print("=" * 70)

