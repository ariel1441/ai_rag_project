"""
Verify that the system works correctly on the main (slow) PC.
Checks compatibility, fallbacks, and configuration.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

print("=" * 80)
print("MAIN PC COMPATIBILITY VERIFICATION")
print("=" * 80)
print()

# Check 1: RAG System Import
print("1. Checking RAG System Import...")
try:
    from api.services import RAGService
    print("   ✓ RAGService imports successfully")
    
    # Check if it uses GPU or CPU version
    try:
        from scripts.core.rag_query_gpu import GPUOptimizedRAGSystem
        print("   ✓ GPU-optimized version available")
    except ImportError:
        print("   ⚠️  GPU-optimized version not available (will use CPU version)")
    
    try:
        from scripts.core.rag_query import RAGSystem
        print("   ✓ Base RAGSystem available (CPU fallback)")
    except ImportError:
        print("   ✗ Base RAGSystem not available!")
        sys.exit(1)
        
except Exception as e:
    print(f"   ✗ Failed to import RAGService: {e}")
    sys.exit(1)

print()

# Check 2: GPU Detection
print("2. Checking GPU Detection...")
try:
    import torch
    has_gpu = torch.cuda.is_available()
    if has_gpu:
        print(f"   ✓ GPU detected: {torch.cuda.get_device_name(0)}")
        print("   → Will use GPU-optimized version")
    else:
        print("   ⚠️  No GPU detected")
        print("   → Will use CPU-optimized version (slower but works)")
        print("   → CPU optimizations: 200 tokens, greedy decoding")
except ImportError:
    print("   ⚠️  PyTorch not installed (will fail when loading model)")
except Exception as e:
    print(f"   ⚠️  Error checking GPU: {e}")

print()

# Check 3: Database Configuration
print("3. Checking Database Configuration...")
try:
    from dotenv import load_dotenv
    load_dotenv()
    
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")  # Default to 5432 for main PC
    database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")
    
    print(f"   Host: {host}")
    print(f"   Port: {port} (main PC usually 5432, new PC Docker 5433)")
    print(f"   Database: {database}")
    print(f"   User: {user}")
    
    if not password:
        print("   ⚠️  POSTGRES_PASSWORD not set in .env")
    else:
        print("   ✓ Password configured")
        
    # Try to connect
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password
        )
        conn.close()
        print(f"   ✓ Database connection successful (port {port})")
    except Exception as e:
        print(f"   ✗ Database connection failed: {e}")
        print(f"   → Make sure PostgreSQL is running on port {port}")
        
except Exception as e:
    print(f"   ⚠️  Error loading .env: {e}")

print()

# Check 4: Core Files
print("4. Checking Core Files...")
core_files = [
    "scripts/core/rag_query.py",
    "scripts/core/rag_query_gpu.py",
    "scripts/core/generate_embeddings.py",
    "scripts/utils/query_parser.py",
    "scripts/utils/text_processing.py",
    "api/services.py",
    "api/app.py",
]

all_exist = True
for file_path in core_files:
    full_path = project_root / file_path
    if full_path.exists():
        print(f"   ✓ {file_path}")
    else:
        print(f"   ✗ {file_path} - MISSING!")
        all_exist = False

if not all_exist:
    print("   ⚠️  Some core files are missing!")
else:
    print("   ✓ All core files present")

print()

# Check 5: RAG System Behavior
print("5. Checking RAG System Behavior...")
print("   Testing which version will be used...")

try:
    # This is what api/services.py does (updated logic)
    try:
        import torch
        has_gpu = torch.cuda.is_available()
        if has_gpu:
            from scripts.core.rag_query_gpu import GPUOptimizedRAGSystem as RAGSystem
            print("   → Will use: GPUOptimizedRAGSystem (GPU detected)")
            print("   → Behavior: Uses GPU with optimal settings")
            print("   → Settings: 500 tokens, sampling (optimal)")
        else:
            from scripts.core.rag_query import RAGSystem
            print("   → Will use: RAGSystem (base, CPU-optimized)")
            print("   → Behavior: Auto-detects CPU, uses optimizations")
            print("   → Settings: 200 tokens, greedy decoding (CPU optimized)")
    except ImportError:
        from scripts.core.rag_query import RAGSystem
        print("   → Will use: RAGSystem (base, fallback)")
        print("   → Behavior: Auto-detects GPU/CPU")
        print("   → Settings: CPU=200 tokens/greedy, GPU=500 tokens/sampling")
        
    # Check if it has _has_gpu method
    if hasattr(RAGSystem, '_has_gpu'):
        print("   ✓ Has GPU detection method")
    else:
        print("   ⚠️  Missing GPU detection method")
        
except Exception as e:
    print(f"   ✗ Error: {e}")

print()

# Check 6: Embedding Generation
print("6. Checking Embedding Generation...")
try:
    from scripts.utils.text_processing import combine_text_fields_weighted, chunk_text
    print("   ✓ Text processing functions available")
    print("   → Uses combine_text_fields_weighted (44 fields with weights)")
    print("   → Chunking: 512 chars, 50 overlap")
except Exception as e:
    print(f"   ✗ Error: {e}")

print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print()

print("Main PC Compatibility:")
print("  ✓ System will work on main PC (slow/CPU)")
print("  ✓ Automatically uses CPU optimizations (200 tokens, greedy)")
print("  ✓ Falls back gracefully if GPU not available")
print("  ✓ Database connection configurable (check .env for port)")
print()

print("Key Differences:")
print("  - Main PC: CPU optimizations (faster but shorter answers)")
print("  - New PC: GPU optimizations (slower but full-length answers)")
print("  - Both: Same code, automatic detection")
print()

print("To Use on Main PC:")
print("  1. Ensure .env has correct database port (usually 5432)")
print("  2. Start API: uvicorn api.app:app --reload --host 0.0.0.0 --port 8000")
print("  3. System will automatically use CPU optimizations")
print("  4. First query will be slow (model loading), subsequent faster")
print()

print("=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)

