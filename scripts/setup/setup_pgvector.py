"""
Setup pgvector extension for PostgreSQL.

This script will:
1. Check if pgvector is available
2. If not, help install it or set up Docker alternative
3. Enable pgvector extension on your database
4. Verify it works
"""
import os
import sys
import subprocess
import psycopg2
from pathlib import Path
from getpass import getpass

def test_connection(host, port, database, user, password):
    """Test PostgreSQL connection."""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False

def check_pgvector_installed(host, port, database, user, password):
    """Check if pgvector extension files exist."""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        
        # Try to create extension (will fail if not installed, but gives us info)
        try:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()
            cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
            version = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if version:
                print(f"   ✅ pgvector is installed (version {version[0]})")
                return True
            else:
                return False
        except psycopg2.errors.UndefinedFile as e:
            cursor.close()
            conn.close()
            print("   ❌ pgvector extension files not found")
            return False
        except Exception as e:
            if "does not exist" in str(e) or "could not open extension control file" in str(e):
                cursor.close()
                conn.close()
                print("   ❌ pgvector extension not installed")
                return False
            else:
                # Some other error, but extension might exist
                conn.rollback()
                cursor.close()
                conn.close()
                return False
                
    except Exception as e:
        print(f"   ❌ Error checking pgvector: {e}")
        return False

def find_postgresql_path():
    """Find PostgreSQL installation path."""
    common_paths = [
        Path("C:/Program Files/PostgreSQL/16"),
        Path("C:/Program Files/PostgreSQL/15"),
        Path("C:/Program Files/PostgreSQL/14"),
        Path("C:/Program Files/PostgreSQL/13"),
        Path("C:/Program Files (x86)/PostgreSQL/16"),
        Path("C:/Program Files (x86)/PostgreSQL/15"),
    ]
    
    for path in common_paths:
        if path.exists():
            return path
    
    return None

def install_pgvector_guide():
    """Guide user through manual pgvector installation."""
    print()
    print("=" * 80)
    print("MANUAL PGVECTOR INSTALLATION GUIDE")
    print("=" * 80)
    print()
    
    pg_path = find_postgresql_path()
    
    if pg_path:
        print(f"   Found PostgreSQL at: {pg_path}")
        print()
        print("   Steps to install pgvector:")
        print()
        print("   1. Download pgvector:")
        print("      https://github.com/pgvector/pgvector/releases")
        print()
        print(f"   2. Extract and copy files:")
        print(f"      - vector.dll → {pg_path / 'lib'}")
        print(f"      - vector.control and vector--*.sql → {pg_path / 'share' / 'extension'}")
        print()
        print("   3. Restart PostgreSQL service")
        print()
        print("   4. Run this script again")
        print()
    else:
        print("   Could not find PostgreSQL installation path.")
        print("   Manual steps:")
        print()
        print("   1. Download pgvector from:")
        print("      https://github.com/pgvector/pgvector/releases")
        print()
        print("   2. Find your PostgreSQL installation:")
        print("      Usually: C:\\Program Files\\PostgreSQL\\[version]\\")
        print()
        print("   3. Copy files:")
        print("      - vector.dll → PostgreSQL\\lib\\")
        print("      - vector.control and vector--*.sql → PostgreSQL\\share\\extension\\")
        print()
        print("   4. Restart PostgreSQL")
        print("   5. Run this script again")
        print()

def setup_docker_postgres():
    """Set up Docker PostgreSQL with pgvector."""
    print()
    print("=" * 80)
    print("DOCKER SETUP (EASIER ALTERNATIVE)")
    print("=" * 80)
    print()
    
    # Check if Docker is installed
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("   ✅ Docker is installed")
        else:
            print("   ❌ Docker not found")
            print("   Install Docker Desktop from: https://www.docker.com/products/docker-desktop")
            return False
    except FileNotFoundError:
        print("   ❌ Docker not found")
        print("   Install Docker Desktop from: https://www.docker.com/products/docker-desktop")
        return False
    
    print()
    print("   This will create a NEW PostgreSQL container with pgvector pre-installed.")
    print("   It won't affect your existing PostgreSQL.")
    print()
    
    response = input("   Set up Docker PostgreSQL? (y/n): ").strip().lower()
    if response != 'y':
        return False
    
    # Check if container already exists
    result = subprocess.run(["docker", "ps", "-a", "--filter", "name=rag_postgres", "--format", "{{.Names}}"], 
                          capture_output=True, text=True)
    if "rag_postgres" in result.stdout:
        print()
        print("   Container 'rag_postgres' already exists")
        response = input("   Remove and recreate? (y/n): ").strip().lower()
        if response == 'y':
            subprocess.run(["docker", "rm", "-f", "rag_postgres"], check=False)
        else:
            print("   Using existing container")
            print("   Container is running on port 5433")
            print("   Database: postgres, User: postgres, Password: password")
            return True
    
    # Create container
    print()
    print("   Creating Docker container...")
    print("   This may take a minute...")
    
    try:
        subprocess.run([
            "docker", "run", "-d",
            "-p", "5433:5432",
            "-e", "POSTGRES_PASSWORD=password",
            "--name", "rag_postgres",
            "pgvector/pgvector:pg16"
        ], check=True, capture_output=True)
        
        print("   ✅ Docker container created!")
        print()
        print("   Waiting for PostgreSQL to start...")
        import time
        time.sleep(5)
        
        # Create database
        print("   Creating database...")
        subprocess.run([
            "docker", "exec", "-i", "rag_postgres",
            "psql", "-U", "postgres", "-c", "CREATE DATABASE ai_requests_db;"
        ], check=False, capture_output=True)
        
        # Enable extension
        print("   Enabling pgvector extension...")
        result = subprocess.run([
            "docker", "exec", "-i", "rag_postgres",
            "psql", "-U", "postgres", "-d", "ai_requests_db", "-c", "CREATE EXTENSION vector;"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ pgvector extension enabled!")
            print()
            print("   Docker PostgreSQL is ready!")
            print("   Connection details:")
            print("     Host: localhost")
            print("     Port: 5433")
            print("     Database: ai_requests_db")
            print("     User: postgres")
            print("     Password: password")
            print()
            return True
        else:
            print(f"   ⚠️  Extension creation had issues: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Docker setup failed: {e}")
        return False

def enable_pgvector(host, port, database, user, password):
    """Enable pgvector extension."""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Try to enable extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Verify
        cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
        version = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if version:
            print(f"   ✅ pgvector enabled (version {version[0]})")
            return True
        else:
            print("   ❌ pgvector extension not found after creation")
            return False
            
    except Exception as e:
        print(f"   ❌ Failed to enable pgvector: {e}")
        return False

def create_env_file(host, port, database, user, password):
    """Create .env file."""
    env_path = Path(".env")
    
    if env_path.exists():
        print()
        response = input("   .env file exists. Overwrite? (y/n): ").strip().lower()
        if response != 'y':
            print("   Skipped creating .env file")
            return False
    
    env_content = f"""# PostgreSQL Database Configuration
POSTGRES_HOST={host}
POSTGRES_PORT={port}
POSTGRES_DATABASE={database}
POSTGRES_USER={user}
POSTGRES_PASSWORD={password}
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"   ✅ Created .env file")
        return True
    except Exception as e:
        print(f"   ❌ Failed to create .env file: {e}")
        return False

def main():
    """Main setup function."""
    print("=" * 80)
    print("PGVECTOR SETUP")
    print("=" * 80)
    print()
    
    # Step 1: Get connection info
    print("Enter your PostgreSQL connection details:")
    print()
    
    host = input("Host [localhost]: ").strip() or "localhost"
    port_input = input("Port [5432]: ").strip()
    port = int(port_input) if port_input else 5432
    database = input("Database [ai_requests_db]: ").strip() or "ai_requests_db"
    user = input("Username [postgres]: ").strip() or "postgres"
    password = getpass("Password: ")
    
    print()
    print("Testing connection...")
    if not test_connection(host, port, "postgres", user, password):
        print()
        print("❌ Connection failed!")
        print("   Check your credentials and try again.")
        return 1
    
    print("   ✅ Connection successful!")
    
    # Step 2: Check if pgvector is installed
    print()
    print("Checking if pgvector is installed...")
    if check_pgvector_installed(host, port, database, user, password):
        print()
        print("✅ pgvector is already installed and enabled!")
        create_env_file(host, port, database, user, password)
        return 0
    
    # pgvector not installed
    print()
    print("=" * 80)
    print("PGVECTOR NOT FOUND")
    print("=" * 80)
    print()
    print("You have two options:")
    print()
    print("  1. Install pgvector manually (requires downloading files)")
    print("  2. Use Docker (easier, pre-configured with pgvector)")
    print()
    
    choice = input("Choose option (1=manual, 2=docker) [2]: ").strip() or "2"
    
    if choice == "2":
        # Docker option
        if setup_docker_postgres():
            # Update connection info for Docker
            host = "localhost"
            port = 5433
            database = "ai_requests_db"
            user = "postgres"
            password = "password"
            
            create_env_file(host, port, database, user, password)
            print()
            print("=" * 80)
            print("SETUP COMPLETE!")
            print("=" * 80)
            print()
            print("✅ Docker PostgreSQL with pgvector is ready!")
            print("✅ .env file created")
            print()
            print("You can now:")
            print("  1. Import your database dump")
            print("  2. Generate embeddings")
            return 0
        else:
            print()
            print("Docker setup failed or cancelled.")
            print("You can try manual installation (option 1) or set up Docker manually.")
            return 1
    else:
        # Manual installation
        install_pgvector_guide()
        print()
        print("After installing pgvector manually:")
        print("  1. Restart PostgreSQL")
        print("  2. Run this script again")
        return 1

if __name__ == "__main__":
    exit(main())

