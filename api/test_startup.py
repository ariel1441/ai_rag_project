"""
Test startup to see what's failing
"""
import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

print("="*80)
print("Testing API Startup")
print("="*80)
print()

try:
    print("1. Testing imports...")
    from api.services import SearchService, RAGService
    print("   ✅ Imports successful")
except Exception as e:
    print(f"   ❌ Import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n2. Testing SearchService initialization...")
    search_service = SearchService()
    print("   ✅ SearchService initialized")
except Exception as e:
    print(f"   ❌ SearchService init failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n3. Testing SearchService database connection...")
    search_service.connect_db()
    print("   ✅ Database connected")
except Exception as e:
    print(f"   ❌ Database connection failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n4. Testing RAGService initialization...")
    rag_service = RAGService()
    print("   ✅ RAGService initialized")
except Exception as e:
    print(f"   ❌ RAGService init failed: {e}")
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n5. Testing FastAPI app import...")
    from api.app import app
    print("   ✅ FastAPI app imported")
except Exception as e:
    print(f"   ❌ FastAPI app import failed: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("✅ All startup tests passed!")
print("="*80)
print("\nYou can now start the server with:")
print("  python -m uvicorn api.app:app --host 127.0.0.1 --port 8000")

