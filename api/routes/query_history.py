"""
Query History API Routes - Optional Feature

This module provides API endpoints for query history and favorites.
It's completely optional and can be disabled without affecting core functionality.

To disable: Remove this router from app.py or set ENABLE_QUERY_HISTORY=false
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.models import QueryHistoryItem, SaveQueryRequest, ToggleFavoriteRequest
from scripts.features.query_history.service import QueryHistoryService

router = APIRouter(prefix="/api/query-history", tags=["query-history"])

# Global service instance
query_history_service: Optional[QueryHistoryService] = None


def get_query_history_service() -> Optional[QueryHistoryService]:
    """Get or create query history service instance."""
    global query_history_service
    
    # Check if feature is enabled
    if os.getenv("ENABLE_QUERY_HISTORY", "false").lower() != "true":
        return None
    
    if query_history_service is None:
        query_history_service = QueryHistoryService()
    
    if not query_history_service.is_enabled():
        return None
    
    return query_history_service


@router.get("/recent", response_model=List[QueryHistoryItem])
async def get_recent_queries(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(10, ge=1, le=50, description="Number of recent queries to return")
):
    """
    Get recent queries for a user.
    Returns last N queries ordered by last_used_at.
    """
    service = get_query_history_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Query history feature is disabled. Set ENABLE_QUERY_HISTORY=true to enable."
        )
    
    queries = service.get_recent_queries(user_id, limit)
    return queries


@router.get("/favorites", response_model=List[QueryHistoryItem])
async def get_favorite_queries(
    user_id: str = Query(..., description="User ID")
):
    """
    Get all favorite queries for a user.
    """
    service = get_query_history_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Query history feature is disabled. Set ENABLE_QUERY_HISTORY=true to enable."
        )
    
    queries = service.get_favorite_queries(user_id)
    return queries


@router.post("/save")
async def save_query(request: SaveQueryRequest):
    """
    Save a query to history.
    If query already exists for user, update last_used_at and increment use_count.
    """
    service = get_query_history_service()
    if not service:
        # Silently fail if disabled (non-breaking)
        return {"success": False, "message": "Query history disabled"}
    
    query_id = service.save_query(
        user_id=request.user_id,
        query_text=request.query_text,
        query_type=request.query_type,
        intent=request.intent,
        entities=request.entities,
        result_count=request.result_count,
        execution_time_ms=request.execution_time_ms
    )
    
    if query_id:
        return {"success": True, "query_id": query_id}
    else:
        return {"success": False, "message": "Failed to save query"}


@router.post("/favorite/{query_id}")
async def toggle_favorite(query_id: int, request: ToggleFavoriteRequest):
    """
    Toggle favorite status for a query.
    """
    service = get_query_history_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Query history feature is disabled"
        )
    
    result = service.toggle_favorite(query_id, request.user_id)
    
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Query not found or access denied"
        )
    
    return {"success": True, "is_favorite": result}


@router.delete("/history/{query_id}")
async def delete_query(
    query_id: int,
    user_id: str = Query(..., description="User ID")
):
    """
    Delete a query from history.
    """
    service = get_query_history_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Query history feature is disabled"
        )
    
    success = service.delete_query(query_id, user_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Query not found or access denied"
        )
    
    return {"success": True}


@router.get("/suggestions", response_model=List[str])
async def get_query_suggestions(
    user_id: str = Query(..., description="User ID"),
    prefix: str = Query(..., description="Query prefix for autocomplete"),
    limit: int = Query(5, ge=1, le=20, description="Number of suggestions")
):
    """
    Get autocomplete suggestions based on user's query history.
    Returns queries that start with prefix, ordered by use_count.
    """
    service = get_query_history_service()
    if not service:
        return []  # Return empty list if disabled (non-breaking)
    
    suggestions = service.get_suggestions(user_id, prefix, limit)
    return suggestions


@router.get("/popular")
async def get_popular_queries(
    limit: int = Query(10, ge=1, le=50, description="Number of popular queries")
):
    """
    Get most popular queries across all users.
    Useful for discovering common searches.
    """
    service = get_query_history_service()
    if not service:
        raise HTTPException(
            status_code=503,
            detail="Query history feature is disabled"
        )
    
    queries = service.get_popular_queries(limit)
    return queries

