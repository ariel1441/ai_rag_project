"""
Automatic pgvector Installation Script

This script will:
1. Detect your PostgreSQL version
2. Download pgvector automatically
3. Copy files to correct locations
4. Restart PostgreSQL
5. Enable the extension in your database
"""
import os
import sys
import subprocess
import psycopg2
import zipfile
import shutil
import requests
from pathlib import Path
from getpass import getpass
import time

def find_postgresql_path():
    """Find PostgreSQL installation path and version."""
    common_paths = [
        ("16", Path("C:/Program Files/PostgreSQL/16")),
        ("15", Path("C:/Program Files/PostgreSQL/15")),
        ("14", Path("C:/Program Files/PostgreSQL/14")),
        ("13", Path("C:/Program Files/PostgreSQL/13")),
        ("16", Path("C:/Program Files (x86)/PostgreSQL/16")),
        ("15", Path("C:/Program Files (x86)/PostgreSQL/15")),
    ]
    
    for version, path in common_paths:
        if path.exists():
            lib_path = path / "lib"
            if lib_path.exists():
                return version, path
    
    return None, None

def get_pgvector_download_url(version):
    """Get pgvector download URL for specific PostgreSQL version."""
    # Try latest release
    base_url = "https://github.com/pgvector/pgvector/releases/download"
    
    # Common versions
    versions_map = {
        "16": "v0.5.1",
        "15": "v0.5.1",
        "14": "v0.5.1",
        "13": "v0.5.0",
    }
    
    pgvector_version = versions_map.get(version, "v0.5.1")
    filename = f"pgvector-{pgvector_version}-pg{version}-windows-x64.zip"
    url = f"{base_url}/{pgvector_version}/{filename}"
    
    return url, filename

def download_file(url, dest_path):
    """Download file from URL."""
    print(f"   Downloading from: {url}")
    print("   This may take a minute...")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r   Progress: {percent:.1f}%", end='', flush=True)
        
        print()  # New line after progress
        return True
    except Exception as e:
        print(f"\n   ❌ Download failed: {e}")
        return False

def extract_zip(zip_path, extract_to):
    """Extract zip file."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return True
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        return False

def copy_files(src_dir, pg_path):
    """Copy pgvector files to PostgreSQL directories."""
    src_path = Path(src_dir)
    
    # Find vector.dll
    dll_file = None
    for file in src_path.rglob("vector.dll"):
        dll_file = file
        break
    
    if not dll_file:
        print("   ❌ vector.dll not found in extracted files")
        return False
    
    # Find extension files
    control_file = None
    sql_files = []
    for file in src_path.rglob("vector.control"):
        control_file = file
    for file in src_path.rglob("vector--*.sql"):
        sql_files.append(file)
    
    if not control_file:
        print("   ❌ vector.control not found in extracted files")
        return False
    
    print("   Copying files...")
    
    # Copy vector.dll to lib
    lib_dir = pg_path / "lib"
    try:
        shutil.copy2(dll_file, lib_dir / "vector.dll")
        print(f"   ✅ Copied vector.dll to {lib_dir}")
    except PermissionError:
        print(f"   ❌ Permission denied copying to {lib_dir}")
        print("   💡 Try running as Administrator")
        return False
    except Exception as e:
        print(f"   ❌ Failed to copy vector.dll: {e}")
        return False
    
    # Copy extension files to share/extension
    ext_dir = pg_path / "share" / "extension"
    try:
        shutil.copy2(control_file, ext_dir / "vector.control")
        print(f"   ✅ Copied vector.control to {ext_dir}")
        
        for sql_file in sql_files:
            shutil.copy2(sql_file, ext_dir / sql_file.name)
            print(f"   ✅ Copied {sql_file.name} to {ext_dir}")
    except PermissionError:
        print(f"   ❌ Permission denied copying to {ext_dir}")
        print("   💡 Try running as Administrator")
        return False
    except Exception as e:
        print(f"   ❌ Failed to copy extension files: {e}")
        return False
    
    return True

def restart_postgresql_service(version):
    """Restart PostgreSQL service."""
    service_names = [
        f"postgresql-x64-{version}",
        f"postgresql-x64-{version}-x64",
        f"postgresql-{version}-x64",
    ]
    
    print("   Restarting PostgreSQL service...")
    
    for service_name in service_names:
        try:
            # Stop service
            subprocess.run(["net", "stop", service_name], 
                         capture_output=True, check=False, timeout=30)
            time.sleep(2)
            # Start service
            result = subprocess.run(["net", "start", service_name], 
                                  capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print(f"   ✅ PostgreSQL service restarted")
                time.sleep(3)  # Wait for service to fully start
                return True
        except subprocess.TimeoutExpired:
            print(f"   ⚠️  Service restart timed out for {service_name}")
        except Exception as e:
            continue
    
    print("   ⚠️  Could not restart service automatically")
    print("   💡 Please restart PostgreSQL manually from Services")
    return False

def enable_extension(host, port, database, user, password):
    """Enable pgvector extension in database."""
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
        
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Verify
        cursor.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector';")
        version = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if version:
            print(f"   ✅ pgvector extension enabled (version {version[0]})")
            return True
        else:
            print("   ❌ Extension not found after enabling")
            return False
            
    except Exception as e:
        print(f"   ❌ Failed to enable extension: {e}")
        return False

def main():
    """Main installation function."""
    print("=" * 80)
    print("AUTOMATIC PGVECTOR INSTALLATION")
    print("=" * 80)
    print()
    
    # Step 1: Find PostgreSQL
    print("Step 1: Finding PostgreSQL installation...")
    pg_version, pg_path = find_postgresql_path()
    
    if not pg_path:
        print("   ❌ Could not find PostgreSQL installation")
        print("   💡 Make sure PostgreSQL is installed")
        return 1
    
    print(f"   ✅ Found PostgreSQL {pg_version} at: {pg_path}")
    
    # Step 2: Check if already installed
    lib_dll = pg_path / "lib" / "vector.dll"
    ext_control = pg_path / "share" / "extension" / "vector.control"
    
    if lib_dll.exists() and ext_control.exists():
        print()
        print("   ℹ️  pgvector files already exist")
        response = input("   Reinstall anyway? (y/n): ").strip().lower()
        if response != 'y':
            print("   Skipping file installation")
            skip_files = True
        else:
            skip_files = False
    else:
        skip_files = False
    
    # Step 3: Download and install files
    if not skip_files:
        print()
        print("Step 2: Downloading pgvector...")
        url, filename = get_pgvector_download_url(pg_version)
        
        # Create temp directory
        temp_dir = Path("temp_pgvector")
        temp_dir.mkdir(exist_ok=True)
        zip_path = temp_dir / filename
        
        if not download_file(url, zip_path):
            print()
            print("   ❌ Download failed")
            print("   💡 You can download manually from:")
            print(f"      {url}")
            return 1
        
        print("   ✅ Download complete")
        
        # Extract
        print()
        print("Step 3: Extracting files...")
        extract_dir = temp_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)
        
        if not extract_zip(zip_path, extract_dir):
            return 1
        
        print("   ✅ Extraction complete")
        
        # Copy files
        print()
        print("Step 4: Installing files to PostgreSQL...")
        if not copy_files(extract_dir, pg_path):
            print()
            print("   ❌ Installation failed")
            print("   💡 Try running this script as Administrator")
            return 1
        
        print("   ✅ Files installed")
        
        # Restart PostgreSQL
        print()
        print("Step 5: Restarting PostgreSQL...")
        restart_postgresql_service(pg_version)
        
        # Cleanup
        print()
        print("Cleaning up temporary files...")
        try:
            shutil.rmtree(temp_dir)
        except:
            pass
    
    # Step 4: Enable extension
    print()
    print("=" * 80)
    print("STEP 6: ENABLE EXTENSION IN DATABASE")
    print("=" * 80)
    print()
    print("Enter your database connection details:")
    print()
    
    host = input("Host [localhost]: ").strip() or "localhost"
    port_input = input("Port [5432]: ").strip()
    port = int(port_input) if port_input else 5432
    database = input("Database [ai_requests_db]: ").strip() or "ai_requests_db"
    user = input("Username [postgres]: ").strip() or "postgres"
    password = getpass("Password: ")
    
    print()
    print("Enabling pgvector extension...")
    
    if enable_extension(host, port, database, user, password):
        print()
        print("=" * 80)
        print("INSTALLATION COMPLETE!")
        print("=" * 80)
        print()
        print("✅ pgvector is installed and enabled!")
        print()
        print("You can now:")
        print("  1. Import your database dump")
        print("  2. Generate embeddings")
        return 0
    else:
        print()
        print("⚠️  Files installed but extension enable failed")
        print("   Try enabling manually in pgAdmin:")
        print("   Right-click Extensions → Create → Extension → vector")
        return 1

if __name__ == "__main__":
    # Check if requests is installed
    try:
        import requests
    except ImportError:
        print("Installing required package: requests")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
        import requests
    
    exit(main())

