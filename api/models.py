"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class SearchRequest(BaseModel):
    """Request model for search endpoint."""
    query: str = Field(..., description="Search query in Hebrew or English")
    top_k: int = Field(20, ge=1, le=100, description="Number of results to return")
    include_details: bool = Field(True, description="Include full request details")


class SearchResponse(BaseModel):
    """Response model for search endpoint."""
    query: str
    intent: str
    entities: Dict[str, Any]
    results: List[Dict[str, Any]]
    total_found: int
    search_time_ms: float


class RAGRequest(BaseModel):
    """Request model for RAG endpoint."""
    query: str = Field(..., description="Question in Hebrew or English")
    top_k: int = Field(20, ge=1, le=100, description="Number of requests to retrieve for context")
    use_llm: bool = Field(True, description="Use LLM for answer generation (if False, returns retrieval only)")


class RAGResponse(BaseModel):
    """Response model for RAG endpoint."""
    query: str
    answer: Optional[str] = None
    requests: List[Dict[str, Any]]
    intent: str
    entities: Dict[str, Any]
    total_retrieved: int
    response_time_ms: float
    model_loaded: bool


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str
    search_system: str
    rag_system: str


# Query History Feature Models (Optional)
class QueryHistoryItem(BaseModel):
    """Model for a query history item."""
    id: int
    query_text: str
    query_type: str
    intent: Optional[str] = None
    result_count: Optional[int] = None
    is_favorite: bool = False
    last_used_at: Optional[str] = None
    use_count: int = 1


class SaveQueryRequest(BaseModel):
    """Request to save a query to history."""
    user_id: str
    query_text: str
    query_type: str
    intent: Optional[str] = None
    entities: Optional[Dict[str, Any]] = None
    result_count: Optional[int] = None
    execution_time_ms: Optional[int] = None


class ToggleFavoriteRequest(BaseModel):
    """Request to toggle favorite status."""
    user_id: str

