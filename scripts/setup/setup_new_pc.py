"""
Setup script for new PC.

Checks prerequisites, verifies database, checks models, and provides setup instructions.
"""
import os
import sys
from pathlib import Path
import subprocess

def check_python():
    """Check Python version."""
    print("1. Checking Python...")
    version = sys.version_info
    if version >= (3, 8):
        print(f"   ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python 3.8+ required (found {version.major}.{version.minor})")
        return False

def check_packages():
    """Check required Python packages."""
    print("\n2. Checking Python packages...")
    packages = {
        'psycopg2': 'psycopg2-binary',
        'sentence_transformers': 'sentence-transformers',
        'numpy': 'numpy',
        'tqdm': 'tqdm',
        'dotenv': 'python-dotenv',
        'transformers': 'transformers',
        'torch': 'torch'
    }
    
    all_ok = True
    for module, package in packages.items():
        try:
            __import__(module)
            print(f"   ✓ {package}")
        except ImportError:
            print(f"   ❌ {package} - Install: pip install {package}")
            all_ok = False
    
    return all_ok

def check_database():
    """Check database connection."""
    print("\n3. Checking database connection...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5433")
        database = os.getenv("POSTGRES_DATABASE")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD")
        
        if not database or not password:
            print("   ⚠️  .env file missing or incomplete")
            print("      Create .env file with database credentials")
            return False
        
        import psycopg2
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        
        # Check pgvector
        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');")
        has_pgvector = cursor.fetchone()[0]
        
        # Check tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('requests', 'request_embeddings')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        print(f"   ✓ Database connection successful")
        print(f"   ✓ pgvector extension: {'installed' if has_pgvector else 'NOT installed'}")
        print(f"   ✓ Tables found: {', '.join(tables) if tables else 'None'}")
        
        if 'request_embeddings' in tables:
            cursor2 = conn.cursor()
            cursor2.execute("SELECT COUNT(*) FROM request_embeddings;")
            count = cursor2.fetchone()[0]
            cursor2.close()
            print(f"   ✓ Embeddings: {count:,} rows")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

def check_models():
    """Check if models are present."""
    print("\n4. Checking models...")
    
    # Check LLM model
    llm_path = Path("models/llm/mistral-7b-instruct")
    if llm_path.exists():
        # Check if model files exist
        model_files = list(llm_path.glob("*.safetensors")) + list(llm_path.glob("*.bin"))
        if model_files:
            total_size = sum(f.stat().st_size for f in model_files)
            size_gb = total_size / (1024**3)
            print(f"   ✓ LLM model found: {size_gb:.2f} GB")
            return True
        else:
            print("   ⚠️  LLM model folder exists but no model files")
            print("      Model will download on first RAG query")
            return False
    else:
        print("   ⚠️  LLM model not found")
        print("      Model will download on first RAG query (~30-60 minutes)")
        return False

def check_embedding_model():
    """Check embedding model cache."""
    print("\n5. Checking embedding model...")
    
    # Check Hugging Face cache
    cache_paths = [
        Path.home() / ".cache" / "huggingface" / "hub",
        Path.home() / ".cache" / "torch" / "sentence_transformers"
    ]
    
    model_name = "sentence-transformers_all-MiniLM-L6-v2"
    found = False
    
    for cache_path in cache_paths:
        if cache_path.exists():
            # Look for model
            for item in cache_path.rglob("*"):
                if model_name in str(item) or "MiniLM" in str(item):
                    found = True
                    break
    
    if found:
        print("   ✓ Embedding model found in cache")
        return True
    else:
        print("   ⚠️  Embedding model not in cache")
        print("      Will download automatically on first use (~2-5 minutes)")
        return False

def main():
    """Main setup check."""
    print("=" * 80)
    print("PROJECT SETUP CHECK - NEW PC")
    print("=" * 80)
    print()
    
    results = {
        'python': check_python(),
        'packages': check_packages(),
        'database': check_database(),
        'llm_model': check_models(),
        'embedding_model': check_embedding_model()
    }
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    all_ok = all(results.values())
    
    if all_ok:
        print("✅ All checks passed! Project is ready to use.")
        print()
        print("You can now:")
        print("  1. Run search: python scripts/core/search.py")
        print("  2. Run RAG: python scripts/core/rag_query.py")
        print("  3. Run API: python api/app.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print()
        
        if not results['python']:
            print("Fix: Install Python 3.8+ from python.org")
        
        if not results['packages']:
            print("Fix: Run: pip install -r requirements.txt")
            print("   Or: pip install psycopg2-binary sentence-transformers numpy tqdm python-dotenv transformers torch")
        
        if not results['database']:
            print("Fix:")
            print("  1. Install PostgreSQL")
            print("  2. Enable pgvector: CREATE EXTENSION vector;")
            print("  3. Import database: pg_restore -d database_name database_backup.dump")
            print("  4. Create .env file with database credentials")
        
        if not results['llm_model']:
            print("Fix:")
            print("  Option 1: Transfer models/llm/ folder from work PC")
            print("  Option 2: Model will download on first RAG query (~30-60 min)")
        
        if not results['embedding_model']:
            print("Fix:")
            print("  Model will download automatically on first use (~2-5 min)")
            print("  No action needed")
    
    print()
    return 0 if all_ok else 1

if __name__ == "__main__":
    exit(main())

