"""
Test script to verify embedding setup requirements and current state.
"""
import os
import sys
from pathlib import Path

def test_requirements():
    """Test if all requirements are met."""
    print("=" * 80)
    print("TESTING EMBEDDING SETUP REQUIREMENTS")
    print("=" * 80)
    print()
    
    results = {
        'python': False,
        'packages': False,
        'database': False,
        'env_file': False,
        'scripts': False
    }
    
    # Test 1: Python version
    print("1. Python Version:")
    print(f"   Version: {sys.version}")
    if sys.version_info >= (3, 8):
        print("   ✓ Python 3.8+ detected")
        results['python'] = True
    else:
        print("   ❌ Python 3.8+ required")
    print()
    
    # Test 2: Required packages
    print("2. Required Packages:")
    packages = {
        'psycopg2': 'psycopg2-binary',
        'sentence_transformers': 'sentence-transformers',
        'numpy': 'numpy',
        'tqdm': 'tqdm',
        'dotenv': 'python-dotenv'
    }
    
    all_ok = True
    for module, package in packages.items():
        try:
            __import__(module)
            print(f"   ✓ {package}")
        except ImportError:
            print(f"   ❌ {package} - Install: pip install {package}")
            all_ok = False
    
    results['packages'] = all_ok
    print()
    
    # Test 3: Database connection
    print("3. Database Connection:")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5433")
        database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD")
        
        if password:
            print(f"   ✓ .env file found")
            print(f"     Host: {host}:{port}")
            print(f"     Database: {database}")
            print(f"     User: {user}")
            
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
                cursor = conn.cursor()
                
                # Check pgvector extension
                cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');")
                has_pgvector = cursor.fetchone()[0]
                
                if has_pgvector:
                    print("   ✓ pgvector extension installed")
                else:
                    print("   ⚠️  pgvector extension NOT installed")
                    print("      Run: CREATE EXTENSION vector;")
                
                # Check requests table
                cursor.execute("""
                    SELECT EXISTS(
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'requests'
                    );
                """)
                has_requests = cursor.fetchone()[0]
                
                if has_requests:
                    cursor.execute("SELECT COUNT(*) FROM requests;")
                    count = cursor.fetchone()[0]
                    print(f"   ✓ 'requests' table exists ({count:,} rows)")
                else:
                    print("   ⚠️  'requests' table NOT found")
                
                cursor.close()
                conn.close()
                results['database'] = True
                
            except psycopg2.OperationalError as e:
                print(f"   ❌ Cannot connect to database: {e}")
            except Exception as e:
                print(f"   ⚠️  Database check failed: {e}")
        else:
            print("   ❌ POSTGRES_PASSWORD not found in .env")
            print("      Create .env file with database credentials")
    except Exception as e:
        print(f"   ❌ Error loading .env: {e}")
    
    print()
    
    # Test 4: .env file
    print("4. Configuration Files:")
    env_file = Path(".env")
    if env_file.exists():
        print("   ✓ .env file exists")
        results['env_file'] = True
    else:
        print("   ⚠️  .env file not found (will use defaults)")
    
    print()
    
    # Test 5: Required scripts
    print("5. Required Scripts:")
    scripts = {
        'generate_embeddings.py': 'scripts/core/generate_embeddings.py',
        'intelligent_field_analysis.py': 'scripts/setup/intelligent_field_analysis.py',
        'text_processing.py': 'scripts/utils/text_processing.py'
    }
    
    all_scripts_ok = True
    for name, path in scripts.items():
        script_path = Path(path)
        if script_path.exists():
            print(f"   ✓ {name}")
        else:
            print(f"   ❌ {name} - Missing at {path}")
            all_scripts_ok = False
    
    results['scripts'] = all_scripts_ok
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    all_ok = all(results.values())
    
    if all_ok:
        print("✅ All requirements met! You can run embedding generation.")
        print()
        print("Next step:")
        print("  python scripts/core/generate_embeddings.py")
    else:
        print("⚠️  Some requirements are missing:")
        for key, value in results.items():
            status = "✓" if value else "❌"
            print(f"  {status} {key}")
        print()
        print("Please fix the issues above before running embedding generation.")
    
    print()
    return all_ok

if __name__ == "__main__":
    test_requirements()

