"""
Database connection utilities.
"""
import psycopg2
import os
from pgvector.psycopg2 import register_vector

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_db_config():
    """
    Get database configuration from environment variables.
    
    Returns:
        dict: Database configuration with keys: host, port, database, user, password
    """
    config = {
        'host': os.getenv("POSTGRES_HOST", "localhost"),
        'port': int(os.getenv("POSTGRES_PORT", "5433")),
        'database': os.getenv("POSTGRES_DATABASE", "ai_requests_db"),
        'user': os.getenv("POSTGRES_USER", "postgres"),
        'password': os.getenv("POSTGRES_PASSWORD")
    }
    
    if not config['password']:
        raise ValueError("POSTGRES_PASSWORD not found in .env file!")
    
    return config


def get_db_connection(register_pgvector=True):
    """
    Get a PostgreSQL database connection.
    
    Args:
        register_pgvector (bool): Whether to register pgvector extension
        
    Returns:
        psycopg2.connection: Database connection object
        
    Raises:
        ValueError: If password is not configured
        psycopg2.Error: If connection fails
    """
    config = get_db_config()
    
    conn = psycopg2.connect(
        host=config['host'],
        port=config['port'],
        database=config['database'],
        user=config['user'],
        password=config['password']
    )
    
    if register_pgvector:
        register_vector(conn)
    
    return conn

