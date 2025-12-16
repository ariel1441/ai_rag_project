"""
Quick API Test Script
Tests the API endpoints to verify everything works.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint."""
    print("="*80)
    print("TEST 1: Health Check")
    print("="*80)
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print("❌ Health check failed")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API - is it running?")
        print("   Run: python api/app.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_search():
    """Test search endpoint."""
    print()
    print("="*80)
    print("TEST 2: Search Endpoint (No LLM needed)")
    print("="*80)
    try:
        payload = {
            "query": "פניות מאור גלילי",
            "top_k": 5,
            "include_details": True
        }
        print(f"Query: {payload['query']}")
        print("Sending request...")
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/search",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        elapsed = time.time() - start_time
        
        print(f"Status: {response.status_code}")
        print(f"Time: {elapsed:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Intent: {data.get('intent')}")
            print(f"Entities: {data.get('entities')}")
            print(f"Total found: {data.get('total_found')}")
            print(f"Search time: {data.get('search_time_ms'):.2f} ms")
            print(f"Results: {len(data.get('results', []))} requests")
            print("✅ Search endpoint works!")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_retrieval_only():
    """Test RAG endpoint with retrieval only (no LLM)."""
    print()
    print("="*80)
    print("TEST 3: RAG Endpoint (Retrieval Only - No LLM)")
    print("="*80)
    try:
        payload = {
            "query": "כמה פניות יש מיניב ליבוביץ?",
            "top_k": 5,
            "use_llm": False
        }
        print(f"Query: {payload['query']}")
        print("Sending request (retrieval only, no LLM)...")
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/rag/query",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        elapsed = time.time() - start_time
        
        print(f"Status: {response.status_code}")
        print(f"Time: {elapsed:.2f} seconds")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Intent: {data.get('intent')}")
            print(f"Entities: {data.get('entities')}")
            print(f"Total retrieved: {data.get('total_retrieved')}")
            print(f"Response time: {data.get('response_time_ms'):.2f} ms")
            print(f"Model loaded: {data.get('model_loaded')}")
            print(f"Answer: {data.get('answer')} (None - retrieval only)")
            print("✅ RAG endpoint (retrieval only) works!")
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("="*80)
    print("API TEST SUITE")
    print("="*80)
    print()
    print("Testing API endpoints...")
    print("(Make sure API server is running: python api/app.py)")
    print()
    
    # Wait a moment for connection
    import time
    time.sleep(1)
    
    results = []
    results.append(("Health Check", test_health()))
    if results[0][1]:  # Only continue if health check passes
        results.append(("Search Endpoint", test_search()))
        results.append(("RAG Retrieval Only", test_rag_retrieval_only()))
    
    print()
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print()
        print("✅ ALL TESTS PASSED!")
    else:
        print()
        print("⚠️  Some tests failed - check errors above")

if __name__ == "__main__":
    main()

