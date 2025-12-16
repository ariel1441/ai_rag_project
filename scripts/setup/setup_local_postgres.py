"""
Setup local PostgreSQL database for RAG project.

This script helps you:
1. Check PostgreSQL connection
2. Create a new database (if needed)
3. Enable pgvector extension
4. Set up local-only configuration
5. Create .env file with credentials
"""
import os
import sys
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

def check_postgres_servers():
    """Check what PostgreSQL servers are running."""
    print("=" * 80)
    print("CHECKING POSTGRESQL SERVERS")
    print("=" * 80)
    print()
    
    # Common PostgreSQL ports
    common_ports = [5432, 5433, 5434]
    
    found_servers = []
    for port in common_ports:
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=port,
                database="postgres",
                user="postgres",
                password="postgres"  # Try default
            )
            conn.close()
            found_servers.append(("localhost", port, "postgres", "postgres"))
            print(f"   ✓ Found server on port {port} (default credentials work)")
        except:
            pass
    
    return found_servers

def create_database(host, port, user, password, db_name):
    """Create a new database."""
    try:
        # Connect to default 'postgres' database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database="postgres",
            user=user,
            password=password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"   ⚠️  Database '{db_name}' already exists")
            response = input(f"   Use existing database '{db_name}'? (y/n): ").strip().lower()
            if response != 'y':
                print("   Cancelled.")
                cursor.close()
                conn.close()
                return False
        else:
            # Create database
            cursor.execute(f'CREATE DATABASE "{db_name}";')
            print(f"   ✅ Created database '{db_name}'")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to create database: {e}")
        return False

def enable_pgvector(host, port, user, password, db_name):
    """Enable pgvector extension."""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=db_name,
            user=user,
            password=password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if extension exists
        cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector';")
        exists = cursor.fetchone()
        
        if exists:
            print("   ✓ pgvector extension already enabled")
        else:
            # Enable extension
            cursor.execute("CREATE EXTENSION vector;")
            print("   ✅ Enabled pgvector extension")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to enable pgvector: {e}")
        print("   Try installing pgvector:")
        print("   - Windows: Download from https://github.com/pgvector/pgvector/releases")
        print("   - Or use Docker: docker run -d -p 5433:5432 pgvector/pgvector:pg16")
        return False

def check_local_only(host, port):
    """Check if PostgreSQL is configured for local-only access."""
    print()
    print("=" * 80)
    print("CHECKING LOCAL-ONLY CONFIGURATION")
    print("=" * 80)
    print()
    
    # Check postgresql.conf (if accessible)
    conf_paths = [
        Path("C:/Program Files/PostgreSQL/16/data/postgresql.conf"),
        Path("C:/Program Files/PostgreSQL/15/data/postgresql.conf"),
        Path("C:/Program Files/PostgreSQL/14/data/postgresql.conf"),
    ]
    
    for conf_path in conf_paths:
        if conf_path.exists():
            print(f"   Found config: {conf_path}")
            try:
                with open(conf_path, 'r') as f:
                    content = f.read()
                    if "listen_addresses = 'localhost'" in content or "listen_addresses = '127.0.0.1'" in content:
                        print("   ✅ Configured for local-only (localhost)")
                    elif "listen_addresses = '*'" in content:
                        print("   ⚠️  Configured to listen on all addresses (not local-only)")
                        print("   💡 To make local-only, edit postgresql.conf:")
                        print("      Change: listen_addresses = '*'")
                        print("      To: listen_addresses = 'localhost'")
                    else:
                        print("   ℹ️  Using default (usually local-only)")
            except Exception as e:
                print(f"   ⚠️  Could not read config: {e}")
            break
    else:
        print("   ℹ️  Could not find postgresql.conf (may need admin access)")
        print("   💡 Default PostgreSQL installation is usually local-only")
    
    print()
    print("   ✅ Your database will only be accessible from this PC")
    print("   ✅ External projects won't be affected")
    print("   ✅ Each database is separate and isolated")

def create_env_file(host, port, database, user, password):
    """Create .env file with database credentials."""
    env_path = Path(".env")
    
    if env_path.exists():
        print()
        response = input("   .env file already exists. Overwrite? (y/n): ").strip().lower()
        if response != 'y':
            print("   Skipped creating .env file")
            return False
    
    env_content = f"""# PostgreSQL Database Configuration
# Local database for RAG project
POSTGRES_HOST={host}
POSTGRES_PORT={port}
POSTGRES_DATABASE={database}
POSTGRES_USER={user}
POSTGRES_PASSWORD={password}
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(env_content)
        print(f"   ✅ Created .env file at {env_path.absolute()}")
        print("   ⚠️  Keep this file secure - it contains your password!")
        return True
    except Exception as e:
        print(f"   ❌ Failed to create .env file: {e}")
        return False

def main():
    """Main setup function."""
    print("=" * 80)
    print("POSTGRESQL SETUP FOR RAG PROJECT")
    print("=" * 80)
    print()
    print("This will help you set up a LOCAL-ONLY database for this project.")
    print("Your external projects won't be affected.")
    print()
    
    # Step 1: Get connection info
    print("=" * 80)
    print("STEP 1: DATABASE CONNECTION INFO")
    print("=" * 80)
    print()
    
    print("Enter your PostgreSQL connection details:")
    print("(Press Enter to use defaults)")
    print()
    
    host = input("Host [localhost]: ").strip() or "localhost"
    port_input = input("Port [5432]: ").strip()
    port = int(port_input) if port_input else 5432
    
    # Try to find existing servers
    print()
    print("Checking for existing PostgreSQL servers...")
    found = check_postgres_servers()
    
    if found:
        print()
        print("Found PostgreSQL servers. You can use one of these or enter different credentials.")
    
    print()
    user = input("Username [postgres]: ").strip() or "postgres"
    password = getpass("Password: ")
    
    # Test connection
    print()
    print("Testing connection to 'postgres' database...")
    if not test_connection(host, port, "postgres", user, password):
        print()
        print("❌ Connection failed!")
        print()
        print("Common issues:")
        print("  1. Wrong password - try resetting PostgreSQL password")
        print("  2. PostgreSQL not running - start it from Services")
        print("  3. Wrong port - check pgAdmin for correct port")
        print()
        print("To reset password:")
        print("  1. Open pgAdmin")
        print("  2. Right-click server → Properties → Connection")
        print("  3. Or edit pg_hba.conf and restart PostgreSQL")
        return 1
    
    print("   ✅ Connection successful!")
    
    # Step 2: Create database
    print()
    print("=" * 80)
    print("STEP 2: CREATE DATABASE")
    print("=" * 80)
    print()
    
    db_name = input("Database name [ai_requests_db]: ").strip() or "ai_requests_db"
    
    if not create_database(host, port, user, password, db_name):
        return 1
    
    # Step 3: Enable pgvector
    print()
    print("=" * 80)
    print("STEP 3: ENABLE PGVECTOR")
    print("=" * 80)
    print()
    
    if not enable_pgvector(host, port, user, password, db_name):
        print()
        print("⚠️  pgvector extension not available")
        print("   You can:")
        print("   1. Install pgvector manually")
        print("   2. Use Docker: docker run -d -p 5433:5432 pgvector/pgvector:pg16")
        print("   3. Continue without pgvector (embeddings won't work)")
        response = input("   Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            return 1
    
    # Step 4: Check local-only
    check_local_only(host, port)
    
    # Step 5: Create .env file
    print()
    print("=" * 80)
    print("STEP 4: CREATE .ENV FILE")
    print("=" * 80)
    print()
    
    create_env_file(host, port, db_name, user, password)
    
    # Summary
    print()
    print("=" * 80)
    print("SETUP COMPLETE!")
    print("=" * 80)
    print()
    print("✅ Database created: " + db_name)
    print("✅ pgvector enabled")
    print("✅ .env file created")
    print()
    print("Next steps:")
    print("  1. Import your database dump:")
    print(f"     pg_restore -h {host} -p {port} -U {user} -d {db_name} -c database_backup.dump")
    print()
    print("  2. Or import CSV data:")
    print("     python scripts/helpers/import_csv_to_postgres.py")
    print()
    print("  3. Generate embeddings:")
    print("     python scripts/core/generate_embeddings.py")
    print()
    
    return 0

if __name__ == "__main__":
    exit(main())

