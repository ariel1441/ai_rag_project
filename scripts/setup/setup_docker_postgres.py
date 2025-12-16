"""
Docker PostgreSQL Setup - EASIEST WAY

This script sets up PostgreSQL with pgvector using Docker.
Everything is pre-installed - no manual steps needed!
"""
import subprocess
import sys
import time
import psycopg2
from getpass import getpass

def check_docker():
    """Check if Docker is installed."""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Docker is installed: {result.stdout.strip()}")
            return True
        else:
            return False
    except FileNotFoundError:
        return False

def install_docker_guide():
    """Guide user to install Docker."""
    print()
    print("=" * 80)
    print("DOCKER NOT FOUND")
    print("=" * 80)
    print()
    print("Docker Desktop is not installed.")
    print()
    print("To install:")
    print("  1. Go to: https://www.docker.com/products/docker-desktop")
    print("  2. Download Docker Desktop for Windows")
    print("  3. Install it (takes 5-10 minutes)")
    print("  4. Restart your computer")
    print("  5. Run this script again")
    print()
    print("Docker Desktop is free and safe to install.")
    print()

def setup_docker_postgres():
    """Set up Docker PostgreSQL with pgvector."""
    print("=" * 80)
    print("DOCKER POSTGRESQL SETUP")
    print("=" * 80)
    print()
    print("This will create a PostgreSQL container with pgvector pre-installed.")
    print("It's completely separate from your existing PostgreSQL.")
    print()
    
    # Check if container exists
    result = subprocess.run(["docker", "ps", "-a", "--filter", "name=rag_postgres", "--format", "{{.Names}}"], 
                          capture_output=True, text=True)
    
    if "rag_postgres" in result.stdout:
        print("⚠️  Container 'rag_postgres' already exists")
        response = input("Remove and recreate? (y/n): ").strip().lower()
        if response == 'y':
            print("Removing old container...")
            subprocess.run(["docker", "rm", "-f", "rag_postgres"], check=False)
        else:
            print("Using existing container...")
            # Check if it's running
            result = subprocess.run(["docker", "ps", "--filter", "name=rag_postgres", "--format", "{{.Names}}"],
                                  capture_output=True, text=True)
            if "rag_postgres" not in result.stdout:
                print("Starting container...")
                subprocess.run(["docker", "start", "rag_postgres"], check=True)
            print("✅ Container is running!")
            return True
    
    # Create container
    print()
    print("Creating Docker container...")
    print("This downloads PostgreSQL with pgvector (takes 2-5 minutes)...")
    print()
    
    try:
        subprocess.run([
            "docker", "run", "-d",
            "-p", "5433:5432",  # Port 5433 (won't conflict with your existing PostgreSQL)
            "-e", "POSTGRES_PASSWORD=password",
            "-e", "POSTGRES_DB=ai_requests_db",
            "--name", "rag_postgres",
            "pgvector/pgvector:pg16"
        ], check=True, capture_output=True)
        
        print("✅ Container created!")
        print()
        print("Waiting for PostgreSQL to start (30 seconds)...")
        time.sleep(30)
        
        # Verify it's running
        result = subprocess.run(["docker", "ps", "--filter", "name=rag_postgres", "--format", "{{.Names}}"],
                              capture_output=True, text=True)
        if "rag_postgres" not in result.stdout:
            print("⚠️  Container not running, trying to start...")
            subprocess.run(["docker", "start", "rag_postgres"], check=True)
            time.sleep(10)
        
        # Enable extension
        print("Enabling pgvector extension...")
        result = subprocess.run([
            "docker", "exec", "-i", "rag_postgres",
            "psql", "-U", "postgres", "-d", "ai_requests_db", "-c", "CREATE EXTENSION IF NOT EXISTS vector;"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ pgvector extension enabled!")
        else:
            print(f"⚠️  Extension enable had issues: {result.stderr}")
            # Try again
            time.sleep(5)
            subprocess.run([
                "docker", "exec", "-i", "rag_postgres",
                "psql", "-U", "postgres", "-d", "ai_requests_db", "-c", "CREATE EXTENSION vector;"
            ], check=False)
        
        print()
        print("=" * 80)
        print("SETUP COMPLETE!")
        print("=" * 80)
        print()
        print("✅ PostgreSQL with pgvector is ready!")
        print()
        print("Connection details:")
        print("  Host: localhost")
        print("  Port: 5433")
        print("  Database: ai_requests_db")
        print("  Username: postgres")
        print("  Password: password")
        print()
        print("This is completely separate from your existing PostgreSQL.")
        print("Your existing PostgreSQL is untouched.")
        print()
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker setup failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_env_file():
    """Create .env file for Docker PostgreSQL."""
    env_content = """# PostgreSQL Database Configuration (Docker)
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DATABASE=ai_requests_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
"""
    
    try:
        with open(".env", 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")
        return True
    except Exception as e:
        print(f"⚠️  Could not create .env file: {e}")
        return False

def test_connection():
    """Test database connection."""
    print()
    print("Testing connection...")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="ai_requests_db",
            user="postgres",
            password="password"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if version:
            print(f"✅ Connection successful! pgvector version: {version[0]}")
            return True
        else:
            print("⚠️  Connected but pgvector not found")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    """Main setup function."""
    print("=" * 80)
    print("DOCKER POSTGRESQL SETUP - EASIEST WAY")
    print("=" * 80)
    print()
    print("This is the EASIEST way to get PostgreSQL with pgvector.")
    print("Everything is automatic - no manual steps!")
    print()
    
    # Check Docker
    print("Checking Docker...")
    if not check_docker():
        install_docker_guide()
        return 1
    
    # Setup
    if setup_docker_postgres():
        create_env_file()
        test_connection()
        print()
        print("=" * 80)
        print("YOU'RE ALL SET!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("  1. Import your database dump:")
        print("     pg_restore -h localhost -p 5433 -U postgres -d ai_requests_db -c database_backup.dump")
        print()
        print("  2. Or import CSV data:")
        print("     python scripts/helpers/import_csv_to_postgres.py")
        print()
        print("  3. Generate embeddings:")
        print("     python scripts/core/generate_embeddings.py")
        print()
        return 0
    else:
        print()
        print("Setup failed. Check the error messages above.")
        return 1

if __name__ == "__main__":
    exit(main())

