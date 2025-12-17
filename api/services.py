"""Service layer for API - wraps core functionality."""
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

# Use GPU-optimized RAG system if GPU is available, fallback to regular (CPU-optimized)
try:
    import torch
    has_gpu = torch.cuda.is_available()
    if has_gpu:
        # GPU available - use GPU-optimized version
        from scripts.core.rag_query_gpu import GPUOptimizedRAGSystem as RAGSystem
    else:
        # No GPU - use CPU-optimized version
        from scripts.core.rag_query import RAGSystem
except (ImportError, Exception):
    # Fallback to regular RAG system if anything fails
    from scripts.core.rag_query import RAGSystem
from scripts.utils.query_parser import QueryParser
import psycopg2
from pgvector.psycopg2 import register_vector
from sentence_transformers import SentenceTransformer
import numpy as np
import json

logger = logging.getLogger(__name__)


class SearchService:
    """Service for search operations."""
    
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.embedding_model = None
        self.config = self._load_config()
        self.query_parser = QueryParser(self.config)
    
    def _load_config(self):
        """Load search configuration."""
        config_path = project_root / "config" / "search_config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load config: {e}")
                return None
        else:
            return None
    
    def connect_db(self):
        """Connect to database."""
        if self.conn:
            return  # Already connected
        
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5433")
        database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD")
        
        if not password:
            raise ValueError("POSTGRES_PASSWORD not in .env!")
        
        self.conn = psycopg2.connect(
            host=host, port=int(port), database=database,
            user=user, password=password
        )
        register_vector(self.conn)
        self.cursor = self.conn.cursor()
        logger.info("Database connected")
    
    def _get_embedding_model(self):
        """Get or load embedding model."""
        if not self.embedding_model:
            self.embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        return self.embedding_model
    
    def search(self, query: str, top_k: int = 20) -> tuple[List[Dict[str, Any]], int]:
        """
        Search for requests using semantic similarity.
        Handles similar requests specially if request ID detected.
        Returns (list of request dictionaries, total_count).
        """
        if not self.conn:
            self.connect_db()
        
        # Parse query (config already passed to constructor)
        parsed = self.query_parser.parse(query)
        query_type = parsed.get('query_type', 'find')
        intent = parsed.get('intent', 'general')
        entities = parsed.get('entities', {})
        target_fields = parsed.get('target_fields', [])
        
        # Special handling for similar requests with request ID
        if query_type == 'similar' and 'request_id' in entities:
            request_id = entities['request_id']
            
            # Find similar requests using request ID
            similar_requests, similarity_scores = self._find_similar_by_request_id(
                request_id, top_k=top_k, similarity_threshold=0.6
            )
            
            # Calculate total count (requests with similarity >= threshold)
            total_count = len(similar_requests)
            
            return similar_requests, total_count
        
        # Build filters first to determine if we need semantic search
        # (We'll generate embedding and temp table only if needed)
        sql_filters = []
        filter_params = []
        
        if 'type_id' in entities:
            type_id = entities['type_id']
            sql_filters.append("r.requesttypeid::TEXT = %s::TEXT")
            filter_params.append(str(type_id))
        
        if 'status_id' in entities:
            status_id = entities['status_id']
            sql_filters.append("r.requeststatusid::TEXT = %s::TEXT")
            filter_params.append(str(status_id))
        
        # Date filtering
        if 'date_range' in entities:
            date_range = entities['date_range']
            # Use requeststatusdate as the date field (adjust if needed)
            # Note: requeststatusdate is TEXT, so we need to cast it
            date_field = "r.requeststatusdate::DATE"
            
            if 'start' in date_range and date_range['start']:
                sql_filters.append(f"{date_field} >= %s::DATE")
                filter_params.append(date_range['start'].isoformat())
            
            if 'end' in date_range and date_range['end']:
                sql_filters.append(f"{date_field} <= %s::DATE")
                filter_params.append(date_range['end'].isoformat())
            
            # Days back filter (alternative to start/end)
            if 'days' in date_range and date_range['days']:
                sql_filters.append(f"{date_field} >= CURRENT_DATE - INTERVAL '%s days'")
                filter_params.append(str(date_range['days']))
        
        # Urgency filtering (requests with close deadline)
        if entities.get('urgency', False):
            # Filter by requeststatusdate close to today (within 7 days)
            # This is a heuristic - adjust based on your business logic
            # Note: requeststatusdate is TEXT, so we need to cast it
            sql_filters.append("r.requeststatusdate IS NOT NULL")
            sql_filters.append("r.requeststatusdate::DATE >= CURRENT_DATE")
            sql_filters.append("r.requeststatusdate::DATE <= CURRENT_DATE + INTERVAL '7 days'")
        
        request_filter_sql = ""
        if sql_filters:
            request_filter_sql = "WHERE " + " AND ".join(sql_filters)
        
        # Build boost SQL for field-specific search (matching search.py pattern)
        boost_cases = []
        
        # If we have target fields and entities, boost exact matches
        if target_fields and entities:
            entity_value = None
            if 'person_name' in entities:
                entity_value = entities['person_name']
            elif 'project_name' in entities:
                entity_value = entities['project_name']
            
            if entity_value:
                # Escape single quotes for SQL
                entity_escaped = entity_value.replace("'", "''")
                
                # Field labels for matching
                field_labels = {
                    'updatedby': 'Updated By',
                    'createdby': 'Created By',
                    'responsibleemployeename': 'Responsible Employee',
                    'contactfirstname': 'Contact First Name',
                    'contactlastname': 'Contact Last Name',
                    'projectname': 'Project',
                    'projectdesc': 'Description'
                }
                
                for field in target_fields:
                    if field in field_labels:
                        label = field_labels[field]
                        boost_cases.append(f"WHEN e.text_chunk LIKE '%{label}: %{entity_escaped}%' THEN 2.0")
                
                # Also boost if entity appears anywhere in chunk
                boost_cases.append(f"WHEN e.text_chunk LIKE '%{entity_escaped}%' THEN 1.5")
        
        # Build boost SQL - add ELSE clause
        if not boost_cases:
            boost_sql = "1.0 as boost"
            order_boost_sql = "1.0"
        else:
            boost_cases.append("ELSE 1.0")  # Add ELSE only once
            boost_sql = "CASE " + " ".join(boost_cases) + " END as boost"
            order_boost_sql = "CASE " + " ".join(boost_cases) + " END"
        
        # Search SQL
        embedding_where = "WHERE e.embedding IS NOT NULL"
        join_sql = ""
        if request_filter_sql:
            join_sql = "INNER JOIN requests r ON e.requestid = r.requestid"
            embedding_where += " AND " + request_filter_sql.replace("WHERE ", "")
        
        # AND Logic: When multiple entities detected, require ALL to be present
        # This fixes the issue where "בקשות מאור גלילי מסוג 10" returns MORE results
        # Instead of fewer (which is what we want with AND logic)
        
        # Count entities to determine if we need AND logic
        structured_entities = ['type_id', 'status_id', 'date_range']
        text_entities = ['person_name', 'project_name']
        
        # Check for structured entities (exclude urgency if it's False)
        has_structured = any(
            key in entities and (key != 'urgency' or entities.get('urgency', False))
            for key in structured_entities
        ) or (entities.get('urgency', False) is True)
        
        has_text = any(key in entities for key in text_entities)
        has_multiple = (has_structured and has_text) or (len([k for k in text_entities if k in entities]) > 1)
        
        # If we have multiple entities, require text entities to be present in text_chunk
        # This implements AND logic: all entities must be present
        # BUT: Only apply this when we have BOTH structured AND text entities
        # For multiple text entities only, we rely on semantic similarity
        if has_multiple and has_structured and has_text:
            text_entity_filters = []
            
            # Require person_name if present
            if 'person_name' in entities:
                person_name = entities['person_name']
                # Escape single quotes for SQL and % for LIKE (when using parameterized queries, use %% to escape %)
                person_escaped = person_name.replace("'", "''").replace("%", "%%")
                # Filter at chunk level - COUNT(DISTINCT) will handle multiple chunks per request
                # Note: We use string interpolation here (not %s), so % needs to be escaped as %%
                text_entity_filters.append(f"e.text_chunk LIKE '%{person_escaped}%'")
            
            # Require project_name if present
            if 'project_name' in entities:
                project_name = entities['project_name']
                # Escape single quotes for SQL and % for LIKE
                project_escaped = project_name.replace("'", "''").replace("%", "%%")
                text_entity_filters.append(f"e.text_chunk LIKE '%{project_escaped}%'")
            
            # Add text entity filters to embedding_where (AND logic)
            # Note: These use string interpolation (not %s), so we need to escape % as %%
            # But when using with parameterized queries, psycopg2 interprets % as placeholders
            # Solution: Escape % as %% in the LIKE patterns
            if text_entity_filters:
                # Escape % in text entity filters for psycopg2 (when mixing with parameterized queries)
                escaped_filters = []
                for filter_expr in text_entity_filters:
                    # Replace % with %% to escape for psycopg2 parameterized queries
                    escaped_filter = filter_expr.replace('%', '%%')
                    escaped_filters.append(escaped_filter)
                embedding_where += " AND (" + " AND ".join(escaped_filters) + ")"
        
        # First, get total count of matching requests (for display)
        # For exact SQL filters (type_id, status_id) without text entities, don't apply similarity threshold
        # The exact filter already ensures relevance - we want ALL matching results
        # For semantic queries (person, project, general), apply similarity threshold to filter noise
        
        # Determine if we should apply similarity threshold
        # Don't apply if: exact SQL filters only (no text entities, no semantic search needed)
        # Do apply if: semantic search (person/project) or general queries
        should_apply_similarity = True
        similarity_threshold = 0.4  # Default
        
        if sql_filters and not has_text:
            # Exact SQL filters only (type_id, status_id, dates) - no semantic search needed
            # Return ALL results matching the exact filter
            should_apply_similarity = False
        elif has_multiple and has_structured and has_text:
            # Both SQL filters AND text entity filters - use lower threshold
            # Strict filters already ensure relevance
            similarity_threshold = 0.2  # 20% - lower because filters are strict
        elif intent in ['person', 'project']:
            # Semantic search for person/project - use higher threshold
            similarity_threshold = 0.5  # 50% for person/project
        else:
            # General semantic queries - use medium threshold
            similarity_threshold = 0.4  # 40% for general semantic queries
        
        # Generate embedding and create temp table only if we need semantic search
        if should_apply_similarity:
            model = self._get_embedding_model()
            query_embedding = model.encode(query, normalize_embeddings=True, convert_to_numpy=True)
            
            # Insert into temp table
            self.cursor.execute("DROP TABLE IF EXISTS temp_query_embedding;")
            self.cursor.execute(
                "CREATE TEMP TABLE temp_query_embedding (embedding vector(384));"
            )
            self.cursor.execute(
                "INSERT INTO temp_query_embedding (embedding) VALUES (%s);",
                (query_embedding.tolist(),)
            )
        
        # Build count SQL
        # SQL filters and text entity filters are already in embedding_where
        if should_apply_similarity:
            # Apply similarity threshold for semantic search
            count_sql = f"""
                SELECT COUNT(DISTINCT e.requestid)
                FROM request_embeddings e
                {join_sql if join_sql else ""}
                CROSS JOIN temp_query_embedding t
                {embedding_where}
                AND (1 - (e.embedding <=> t.embedding)) >= {similarity_threshold}
            """
        else:
            # No similarity threshold - exact SQL filter only
            # Don't need temp_query_embedding or similarity check
            count_sql = f"""
                SELECT COUNT(DISTINCT e.requestid)
                FROM request_embeddings e
                {join_sql if join_sql else ""}
                {embedding_where}
            """
        
        # Execute count query
        # Note: When we have text entity filters (has_multiple), we can't use parameterized queries
        # because psycopg2 interprets % in LIKE '%...%' as parameter placeholders
        # Solution: If we have text entity filters, interpolate SQL filter values directly (with proper escaping)
        # Otherwise, use parameterized queries for safety
        try:
            if has_multiple and has_structured and has_text and filter_params:
                # We have text entity filters - can't use parameterized queries (psycopg2 interprets % in LIKE as params)
                # Interpolate SQL filter values directly (they're already safe - type_id/status_id are integers)
                # Escape the SQL properly
                count_sql_interpolated = count_sql
                for i, param in enumerate(filter_params):
                    # Replace %s with the actual value (safe because type_id/status_id are integers/strings from our parser)
                    # Escape single quotes if it's a string
                    if isinstance(param, str):
                        param_escaped = param.replace("'", "''")
                        count_sql_interpolated = count_sql_interpolated.replace('%s', f"'{param_escaped}'", 1)
                    else:
                        count_sql_interpolated = count_sql_interpolated.replace('%s', str(param), 1)
                self.cursor.execute(count_sql_interpolated)
            elif filter_params:
                # No text entity filters - safe to use parameterized queries
                self.cursor.execute(count_sql, tuple(filter_params))
            else:
                # No parameters - execute directly
                self.cursor.execute(count_sql)
            total_count = self.cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Count query failed. SQL: {count_sql[:500]}, Params: {filter_params}, Error: {str(e)}")
            raise
        
        # Now get top results
        # Note: embedding_where already includes:
        # - SQL filters (type_id, status_id, dates) when present
        # - Text entity filters (person_name, project_name) when has_multiple is True
        # Apply similarity threshold only if needed (same logic as count query)
        if should_apply_similarity:
            # Semantic search - apply similarity threshold
            search_sql = f"""
                SELECT 
                    e.requestid,
                    e.chunk_index,
                    1 - (e.embedding <=> t.embedding) as similarity,
                    {boost_sql}
                FROM request_embeddings e
                {join_sql if join_sql else ""}
                CROSS JOIN temp_query_embedding t
                {embedding_where}
                AND (1 - (e.embedding <=> t.embedding)) >= {similarity_threshold}
                ORDER BY (1 - (e.embedding <=> t.embedding)) * ({order_boost_sql}) DESC
                LIMIT {top_k * 3};
            """
        else:
            # Exact SQL filter only - no similarity threshold, order by boost only
            # Use a simple ordering (by requestid or chunk_index) since we don't have similarity
            search_sql = f"""
                SELECT 
                    e.requestid,
                    e.chunk_index,
                    1.0 as similarity,
                    {boost_sql}
                FROM request_embeddings e
                {join_sql if join_sql else ""}
                {embedding_where}
                ORDER BY e.requestid DESC, e.chunk_index
                LIMIT {top_k * 3};
            """
        
        # Execute search query - same logic as count query
        try:
            if has_multiple and has_structured and has_text and filter_params:
                # Interpolate SQL filter values directly (same as count query)
                search_sql_interpolated = search_sql
                for i, param in enumerate(filter_params):
                    if isinstance(param, str):
                        param_escaped = param.replace("'", "''")
                        search_sql_interpolated = search_sql_interpolated.replace('%s', f"'{param_escaped}'", 1)
                    else:
                        search_sql_interpolated = search_sql_interpolated.replace('%s', str(param), 1)
                self.cursor.execute(search_sql_interpolated)
            elif filter_params:
                # No text entity filters - safe to use parameterized queries
                self.cursor.execute(search_sql, tuple(filter_params))
            else:
                # No parameters - execute directly
                self.cursor.execute(search_sql)
        except Exception as e:
            logger.error(f"Search query failed. SQL: {search_sql[:500]}, Params: {filter_params}, Error: {str(e)}")
            raise
        
        chunk_results = self.cursor.fetchall()
        
        # Group by request ID
        request_scores = {}
        for req_id, chunk_idx, similarity, boost in chunk_results:
            # Convert boost to float to avoid type errors
            boost_float = float(boost) if boost else 1.0
            similarity_float = float(similarity) if similarity else 0.0
            
            if req_id not in request_scores:
                request_scores[req_id] = {
                    'best_similarity': similarity_float,
                    'best_chunk': chunk_idx,
                    'boost': boost_float
                }
            else:
                if similarity_float > request_scores[req_id]['best_similarity']:
                    request_scores[req_id]['best_similarity'] = similarity_float
                    request_scores[req_id]['best_chunk'] = chunk_idx
        
        # Get top requests
        sorted_requests = sorted(
            request_scores.items(),
            key=lambda x: x[1]['best_similarity'] * x[1]['boost'],
            reverse=True
        )
        
        unique_request_ids = [req_id for req_id, _ in sorted_requests[:top_k]]
        
        # Get total count before filtering to top_k (if we haven't already)
        # This is a fallback - we should have already gotten total_count above
        # But if we're here, we need to get it (shouldn't happen in normal flow)
        if 'total_count' not in locals():
            if sql_filters:
                # Filtered query - count based on filter
                count_sql = f"""
                    SELECT COUNT(DISTINCT e.requestid)
                    FROM request_embeddings e
                    {join_sql}
                    CROSS JOIN temp_query_embedding t
                    {embedding_where}
                """
            else:
                # Semantic query - apply similarity threshold
                # Use same logic as above (intent-based threshold)
                if intent in ['person', 'project']:
                    similarity_threshold = 0.5  # 50% for person/project
                else:
                    similarity_threshold = 0.4  # 40% for general
                count_sql = f"""
                    SELECT COUNT(DISTINCT e.requestid)
                    FROM request_embeddings e
                    {join_sql}
                    CROSS JOIN temp_query_embedding t
                    {embedding_where}
                    AND (1 - (e.embedding <=> t.embedding)) >= {similarity_threshold}
                """
            
            if filter_params:
                self.cursor.execute(count_sql, tuple(filter_params))
            else:
                self.cursor.execute(count_sql)
            total_count = self.cursor.fetchone()[0]
        
        if not unique_request_ids:
            self.cursor.execute("DROP TABLE IF EXISTS temp_query_embedding;")
            return [], total_count
        
        # Fetch full request data
        placeholders = ','.join(['%s'] * len(unique_request_ids))
        self.cursor.execute(
            f"""
            SELECT requestid, projectname, projectdesc, areadesc, remarks,
                   updatedby, createdby, responsibleemployeename,
                   contactfirstname, contactlastname, contactemail,
                   requesttypeid, requeststatusid, requeststatusdate
            FROM requests
            WHERE requestid IN ({placeholders})
            """,
            tuple(unique_request_ids)
        )
        
        requests_data = self.cursor.fetchall()
        requests_dict = {row[0]: row for row in requests_data}
        
        # Build results
        results = []
        for req_id in unique_request_ids:
            score_info = request_scores[req_id]
            similarity = score_info['best_similarity']
            boost = score_info['boost']
            
            result = {
                'requestid': req_id,
                'similarity': float(similarity),
                'boost': float(boost)
            }
            
            if req_id in requests_dict:
                row = requests_dict[req_id]
                result.update({
                    'projectname': row[1],
                    'projectdesc': row[2],
                    'areadesc': row[3],
                    'remarks': row[4],
                    'updatedby': row[5],
                    'createdby': row[6],
                    'responsibleemployeename': row[7],
                    'contactfirstname': row[8],
                    'contactlastname': row[9],
                    'contactemail': row[10],
                    'requesttypeid': row[11],
                    'requeststatusid': row[12],
                    'requeststatusdate': str(row[13]) if row[13] else None
                })
            
            results.append(result)
        
        # Clean up
        self.cursor.execute("DROP TABLE IF EXISTS temp_query_embedding;")
        
        return results, total_count
    
    def _find_similar_by_request_id(self, request_id: str, top_k: int = 20, 
                                    similarity_threshold: float = 0.6) -> tuple[List[Dict], Dict[str, float]]:
        """
        Find requests similar to a specific request ID.
        Uses the actual request's embedding, not query text.
        
        Args:
            request_id: Source request ID
            top_k: Number of similar requests to return
            similarity_threshold: Minimum similarity score (0.0-1.0)
            
        Returns:
            (list of similar requests, similarity scores dict)
        """
        if not self.conn:
            self.connect_db()
        
        # 1. Find source request's embedding
        self.cursor.execute("""
            SELECT embedding, requestid
            FROM request_embeddings
            WHERE requestid = %s
            ORDER BY chunk_index
            LIMIT 1
        """, (request_id,))
        
        source_result = self.cursor.fetchone()
        if not source_result:
            logger.warning(f"Request ID {request_id} not found in embeddings")
            return [], {}
        
        source_embedding = source_result[0]
        
        # 2. Find similar requests (exclude source)
        embedding_str = '[' + ','.join(map(str, source_embedding)) + ']'
        self.cursor.execute("""
            SELECT 
                e.requestid,
                e.chunk_index,
                1 - (e.embedding <=> %s::vector) as similarity
            FROM request_embeddings e
            WHERE e.embedding IS NOT NULL
              AND e.requestid != %s
              AND (1 - (e.embedding <=> %s::vector)) >= %s
            ORDER BY e.embedding <=> %s::vector
            LIMIT %s
        """, (embedding_str, request_id, embedding_str, similarity_threshold, embedding_str, top_k * 3))
        
        chunk_results = self.cursor.fetchall()
        
        # Group by request ID, keep best similarity
        request_scores = {}
        for req_id, chunk_idx, similarity in chunk_results:
            if req_id not in request_scores:
                request_scores[req_id] = {
                    'best_similarity': similarity,
                    'best_chunk': chunk_idx
                }
            else:
                if similarity > request_scores[req_id]['best_similarity']:
                    request_scores[req_id]['best_similarity'] = similarity
                    request_scores[req_id]['best_chunk'] = chunk_idx
        
        # Sort by similarity
        sorted_requests = sorted(
            request_scores.items(),
            key=lambda x: x[1]['best_similarity'],
            reverse=True
        )[:top_k]
        
        # Get unique request IDs
        unique_request_ids = [req_id for req_id, _ in sorted_requests]
        similarity_scores = {req_id: data['best_similarity'] for req_id, data in sorted_requests}
        
        if not unique_request_ids:
            return [], {}
        
        # Fetch full request data
        placeholders = ','.join(['%s'] * len(unique_request_ids))
        self.cursor.execute(f"""
            SELECT 
                requestid, projectname, projectdesc, areadesc, remarks,
                updatedby, createdby, responsibleemployeename,
                contactfirstname, contactlastname, contactemail,
                requesttypeid, requeststatusid, requeststatusdate
            FROM requests
            WHERE requestid IN ({placeholders})
        """, tuple(unique_request_ids))
        
        rows = self.cursor.fetchall()
        
        # Build results with similarity scores
        results = []
        for row in rows:
            req_id = str(row[0])
            similarity = similarity_scores.get(req_id, 0.0)
            
            result = {
                'requestid': req_id,
                'similarity': float(similarity),
                'boost': 1.0,
                'projectname': row[1],
                'projectdesc': row[2],
                'areadesc': row[3],
                'remarks': row[4],
                'updatedby': row[5],
                'createdby': row[6],
                'responsibleemployeename': row[7],
                'contactfirstname': row[8],
                'contactlastname': row[9],
                'contactemail': row[10],
                'requesttypeid': row[11],
                'requeststatusid': row[12],
                'requeststatusdate': str(row[13]) if row[13] else None
            }
            results.append(result)
        
        # Sort by similarity (maintain order)
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        return results, similarity_scores
    
    def close(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        self.conn = None
        self.cursor = None


class RAGService:
    """Service for RAG operations."""
    
    def __init__(self):
        self.rag_system: Optional[RAGSystem] = None
    
    def get_rag_system(self) -> RAGSystem:
        """Get or initialize RAG system."""
        if not self.rag_system:
            try:
                logger.info("Initializing RAG system (lazy loading)...")
                self.rag_system = RAGSystem()
                self.rag_system.connect_db()
                logger.info("RAG system initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize RAG system: {e}", exc_info=True)
                raise
        return self.rag_system
    
    def query(self, query: str, top_k: int = 20, use_llm: bool = True) -> Dict[str, Any]:
        """
        Execute RAG query.
        If use_llm=False, returns retrieval only.
        """
        if not use_llm:
            # Use search service for retrieval only
            search_service = SearchService()
            search_service.connect_db()
            results = search_service.search(query, top_k)
            parsed = search_service.query_parser.parse(query)
            search_service.close()
            
            return {
                'answer': None,
                'requests': results,
                'intent': parsed.get('intent', 'general'),
                'entities': parsed.get('entities', {})
            }
        
        # Full RAG with LLM - with error handling
        try:
            logger.info(f"Getting RAG system for query: '{query[:50]}...'")
            rag = self.get_rag_system()
            logger.info("RAG system obtained, executing query...")
            
            # Wrap model loading in try-except to prevent process crash
            try:
                result = rag.query(query, top_k=top_k)
                logger.info("RAG query completed successfully")
                
                # Debug: Log answer for troubleshooting
                answer = result.get('answer')
                if answer:
                    logger.info(f"Answer generated: {len(answer)} characters, preview: {answer[:100]}...")
                else:
                    logger.warning("⚠️  No answer in result! Result keys: " + str(result.keys()))
                
                return result
            except (MemoryError, RuntimeError, OSError) as model_error:
                # Model loading/generation failed - catch before it crashes process
                error_msg = str(model_error)
                logger.error(f"Model loading/generation failed: {error_msg}", exc_info=True)
                
                # Check if it's a memory issue
                if any(keyword in error_msg.lower() for keyword in [
                    "memory", "alloc", "out of memory", "cannot allocate",
                    "not enough", "fragmentation"
                ]):
                    error_msg = "Memory allocation failed during model loading. This is likely due to memory fragmentation. Try restarting your computer, or use 'RAG - רק חיפוש' option instead."
                
                # Fallback to retrieval only
                logger.warning("Falling back to retrieval only due to model error")
                search_service = SearchService()
                search_service.connect_db()
                results = search_service.search(query, top_k)
                parsed = search_service.query_parser.parse(query)
                search_service.close()
                
                return {
                    'answer': None,
                    'requests': results,
                    'intent': parsed.get('intent', 'general'),
                    'entities': parsed.get('entities', {}),
                    'error': error_msg
                }
        except Exception as e:
            logger.error(f"RAG query with LLM failed: {e}", exc_info=True)
            # Fallback to retrieval only if LLM fails
            logger.warning("Falling back to retrieval only due to LLM error")
            search_service = SearchService()
            search_service.connect_db()
            results = search_service.search(query, top_k)
            parsed = search_service.query_parser.parse(query)
            search_service.close()
            
            return {
                'answer': None,
                'requests': results,
                'intent': parsed.get('intent', 'general'),
                'entities': parsed.get('entities', {}),
                'error': f'LLM generation failed: {str(e)}. Showing retrieval results only.'
            }
    
    def close(self):
        """Close RAG system."""
        if self.rag_system:
            self.rag_system.close()
            self.rag_system = None

