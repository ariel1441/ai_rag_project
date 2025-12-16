"""
Query History Service - Modular Feature

This service handles query history and favorites.
It's completely separate from core search functionality.
"""
import os
import json
import psycopg2
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class QueryHistoryService:
    """
    Service for managing query history and favorites.
    
    This is a modular feature - can be enabled/disabled without affecting
    core search functionality.
    """
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.enabled = os.getenv("ENABLE_QUERY_HISTORY", "false").lower() == "true"
    
    def is_enabled(self) -> bool:
        """Check if query history feature is enabled."""
        return self.enabled
    
    def connect_db(self):
        """Connect to database."""
        if not self.enabled:
            logger.warning("Query history feature is disabled")
            return False
        
        if self.conn:
            return True
        
        try:
            host = os.getenv("POSTGRES_HOST", "localhost")
            port = os.getenv("POSTGRES_PORT", "5433")
            database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
            user = os.getenv("POSTGRES_USER", "postgres")
            password = os.getenv("POSTGRES_PASSWORD")
            
            if not password:
                logger.error("POSTGRES_PASSWORD not set - query history disabled")
                self.enabled = False
                return False
            
            self.conn = psycopg2.connect(
                host=host, port=int(port), database=database,
                user=user, password=password
            )
            self.cursor = self.conn.cursor()
            
            # Check if table exists (graceful degradation)
            self.cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'user_query_history'
                )
            """)
            table_exists = self.cursor.fetchone()[0]
            
            if not table_exists:
                logger.warning("Query history table does not exist - run migration first")
                self.enabled = False
                return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database for query history: {e}")
            self.enabled = False
            return False
    
    def save_query(
        self,
        user_id: str,
        query_text: str,
        query_type: str,
        intent: Optional[str] = None,
        entities: Optional[dict] = None,
        result_count: Optional[int] = None,
        execution_time_ms: Optional[int] = None
    ) -> Optional[int]:
        """
        Save or update query in history.
        Returns query ID if successful, None if disabled or error.
        """
        if not self.enabled:
            return None
        
        if not self.connect_db():
            return None
        
        try:
            # Check if query already exists for this user
            self.cursor.execute("""
                SELECT id, use_count FROM user_query_history
                WHERE user_id = %s AND query_text = %s
            """, (user_id, query_text))
            
            existing = self.cursor.fetchone()
            
            if existing:
                # Update existing query
                query_id, current_count = existing
                self.cursor.execute("""
                    UPDATE user_query_history
                    SET last_used_at = CURRENT_TIMESTAMP,
                        use_count = use_count + 1,
                        result_count = COALESCE(%s, result_count),
                        execution_time_ms = COALESCE(%s, execution_time_ms)
                    WHERE id = %s
                """, (result_count, execution_time_ms, query_id))
                self.conn.commit()
                return query_id
            else:
                # Insert new query
                self.cursor.execute("""
                    INSERT INTO user_query_history
                    (user_id, query_text, query_type, intent, entities, 
                     result_count, execution_time_ms, use_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                    RETURNING id
                """, (
                    user_id, query_text, query_type, intent,
                    json.dumps(entities) if entities else None,
                    result_count, execution_time_ms
                ))
                query_id = self.cursor.fetchone()[0]
                self.conn.commit()
                return query_id
        except Exception as e:
            logger.error(f"Error saving query to history: {e}")
            if self.conn:
                self.conn.rollback()
            return None
    
    def get_recent_queries(self, user_id: str, limit: int = 10) -> List[dict]:
        """Get recent queries for user."""
        if not self.enabled or not self.connect_db():
            return []
        
        try:
            self.cursor.execute("""
                SELECT id, query_text, query_type, intent, result_count,
                       is_favorite, last_used_at, use_count
                FROM user_query_history
                WHERE user_id = %s
                ORDER BY last_used_at DESC
                LIMIT %s
            """, (user_id, limit))
            
            results = []
            for row in self.cursor.fetchall():
                results.append({
                    'id': row[0],
                    'query_text': row[1],
                    'query_type': row[2],
                    'intent': row[3],
                    'result_count': row[4],
                    'is_favorite': row[5],
                    'last_used_at': row[6].isoformat() if row[6] else None,
                    'use_count': row[7]
                })
            return results
        except Exception as e:
            logger.error(f"Error getting recent queries: {e}")
            return []
    
    def get_favorite_queries(self, user_id: str) -> List[dict]:
        """Get favorite queries for user."""
        if not self.enabled or not self.connect_db():
            return []
        
        try:
            self.cursor.execute("""
                SELECT id, query_text, query_type, intent, result_count,
                       last_used_at, use_count
                FROM user_query_history
                WHERE user_id = %s AND is_favorite = TRUE
                ORDER BY last_used_at DESC
            """, (user_id,))
            
            results = []
            for row in self.cursor.fetchall():
                results.append({
                    'id': row[0],
                    'query_text': row[1],
                    'query_type': row[2],
                    'intent': row[3],
                    'result_count': row[4],
                    'last_used_at': row[5].isoformat() if row[5] else None,
                    'use_count': row[6]
                })
            return results
        except Exception as e:
            logger.error(f"Error getting favorite queries: {e}")
            return []
    
    def toggle_favorite(self, query_id: int, user_id: str) -> Optional[bool]:
        """Toggle favorite status."""
        if not self.enabled or not self.connect_db():
            return None
        
        try:
            self.cursor.execute("""
                UPDATE user_query_history
                SET is_favorite = NOT is_favorite
                WHERE id = %s AND user_id = %s
                RETURNING is_favorite
            """, (query_id, user_id))
            
            result = self.cursor.fetchone()
            if result:
                self.conn.commit()
                return result[0]
            return None
        except Exception as e:
            logger.error(f"Error toggling favorite: {e}")
            if self.conn:
                self.conn.rollback()
            return None
    
    def get_suggestions(self, user_id: str, prefix: str, limit: int = 5) -> List[str]:
        """Get autocomplete suggestions."""
        if not self.enabled or not self.connect_db():
            return []
        
        try:
            self.cursor.execute("""
                SELECT DISTINCT query_text, MAX(use_count) as max_count
                FROM user_query_history
                WHERE user_id = %s AND query_text ILIKE %s
                GROUP BY query_text
                ORDER BY max_count DESC, query_text
                LIMIT %s
            """, (user_id, f'{prefix}%', limit))
            
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return []
    
    def get_popular_queries(self, limit: int = 10) -> List[dict]:
        """Get most popular queries across all users."""
        if not self.enabled or not self.connect_db():
            return []
        
        try:
            self.cursor.execute("""
                SELECT query_text, SUM(use_count) as total_uses,
                       COUNT(DISTINCT user_id) as unique_users
                FROM user_query_history
                GROUP BY query_text
                ORDER BY total_uses DESC
                LIMIT %s
            """, (limit,))
            
            results = []
            for row in self.cursor.fetchall():
                results.append({
                    'query_text': row[0],
                    'total_uses': row[1],
                    'unique_users': row[2]
                })
            return results
        except Exception as e:
            logger.error(f"Error getting popular queries: {e}")
            return []
    
    def delete_query(self, query_id: int, user_id: str) -> bool:
        """Delete a query from history."""
        if not self.enabled or not self.connect_db():
            return False
        
        try:
            self.cursor.execute("""
                DELETE FROM user_query_history
                WHERE id = %s AND user_id = %s
            """, (query_id, user_id))
            
            deleted = self.cursor.rowcount > 0
            self.conn.commit()
            return deleted
        except Exception as e:
            logger.error(f"Error deleting query: {e}")
            if self.conn:
                self.conn.rollback()
            return False

