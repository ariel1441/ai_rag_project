"""
FastAPI Application for RAG System
Designed for internal server deployment with multi-user support.
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os
import sys
from pathlib import Path
from typing import Optional, List
import logging
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

# Import our services
from api.services import SearchService, RAGService
from api.models import SearchRequest, SearchResponse, RAGRequest, RAGResponse, HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global instances (shared across requests)
search_service: Optional[SearchService] = None
rag_service: Optional[RAGService] = None

# Simple API key authentication (replace with your auth system)
VALID_API_KEYS = os.getenv("API_KEYS", "").split(",") if os.getenv("API_KEYS") else []
# For development, allow empty if no keys set
REQUIRE_AUTH = os.getenv("REQUIRE_AUTH", "false").lower() == "true"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global search_service, rag_service
    
    # Startup
    logger.info("Starting API server...")
    try:
        # Initialize search service (lightweight, always available)
        logger.info("Initializing search service...")
        search_service = SearchService()
        search_service.connect_db()
        logger.info("✅ Search service initialized")
        
        # RAG service will be loaded on first use (lazy loading)
        # Model loads only when first RAG query with LLM is made
        logger.info("Initializing RAG service (no model loading yet)...")
        rag_service = RAGService()
        logger.info("✅ RAG service initialized (model will load on first query)")
        
        logger.info("✅ API server ready")
    except Exception as e:
        logger.error(f"❌ Failed to initialize: {e}", exc_info=True)
        # Don't raise - let server start anyway, just log the error
        # This way search service can still work even if RAG fails
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Set to None so we know it failed
        if 'search_service' not in locals() or search_service is None:
            search_service = None
        if 'rag_service' not in locals() or rag_service is None:
            rag_service = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down API server...")
    if search_service:
        search_service.close()
    if rag_service:
        rag_service.close()
    logger.info("✅ API server shut down")


# Create FastAPI app
app = FastAPI(
    title="AI Requests RAG API",
    description="Internal API for semantic search and RAG queries on company requests",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware (configure for your internal network)
# Allow all origins for local development (including file://)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for local dev (change for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication dependency
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key (simple implementation - replace with your auth system)."""
    if not REQUIRE_AUTH:
        return True  # Development mode
    
    if not VALID_API_KEYS:
        logger.warning("No API keys configured - allowing all requests")
        return True
    
    if not x_api_key or x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    
    return True


# Models imported from api.models

# Optional Feature: Query History
# This feature can be enabled/disabled via ENABLE_QUERY_HISTORY env var
if os.getenv("ENABLE_QUERY_HISTORY", "false").lower() == "true":
    try:
        from api.routes.query_history import router as query_history_router
        app.include_router(query_history_router)
        logger.info("✅ Query history feature enabled")
    except Exception as e:
        logger.warning(f"⚠️  Query history feature failed to load: {e}")
        logger.info("   Continuing without query history feature")
else:
    logger.info("ℹ️  Query history feature disabled (set ENABLE_QUERY_HISTORY=true to enable)")


# Health check
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        search_system="ready" if search_service else "not initialized",
        rag_system="ready" if rag_service and rag_service.rag_system else "lazy loading"
    )


# Search endpoint (retrieval only, no LLM)
@app.post("/api/search", response_model=SearchResponse)
async def search_requests(
    request: SearchRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    Search requests using semantic similarity.
    Returns list of relevant requests without LLM generation.
    Fast - works without loading LLM model.
    """
    import time
    start_time = time.time()
    
    try:
        if not search_service:
            raise HTTPException(status_code=503, detail="Search service not initialized")
        
        # Search (returns results and total_count)
        results, total_count = search_service.search(request.query, top_k=request.top_k)
        
        # Parse query for intent/entities (config already passed to constructor)
        parsed = search_service.query_parser.parse(request.query)
        
        # Format results
        formatted_results = []
        for req in results:
            result_item = {
                "requestid": req.get('requestid'),
                "similarity": req.get('similarity', 0),
                "boost": req.get('boost', 1.0)
            }
            
            if request.include_details:
                result_item.update({
                    "projectname": req.get('projectname'),
                    "updatedby": req.get('updatedby'),
                    "createdby": req.get('createdby'),
                    "responsibleemployeename": req.get('responsibleemployeename'),
                    "requesttypeid": req.get('requesttypeid'),
                    "requeststatusid": req.get('requeststatusid'),
                    "requeststatusdate": req.get('requeststatusdate'),
                    "areadesc": req.get('areadesc'),
                    "remarks": req.get('remarks'),
                    "contactemail": req.get('contactemail'),
                })
            
            formatted_results.append(result_item)
        
        search_time = (time.time() - start_time) * 1000
        
        logger.info(f"Search query: '{request.query}' - Found {len(results)} results in {search_time:.2f}ms")
        
        # Optional: Save query to history (non-breaking, fails silently if disabled)
        try:
            if os.getenv("ENABLE_QUERY_HISTORY", "false").lower() == "true":
                from scripts.features.query_history.service import QueryHistoryService
                history_service = QueryHistoryService()
                if history_service.is_enabled():
                    # Get user_id from request or use default
                    user_id = getattr(request, 'user_id', 'anonymous')
                    history_service.save_query(
                        user_id=user_id,
                        query_text=request.query,
                        query_type='search',
                        intent=parsed.get('intent'),
                        entities=parsed.get('entities'),
                        result_count=total_count,
                        execution_time_ms=int(search_time)
                    )
        except Exception as e:
            # Silently fail - don't break search if history fails
            logger.debug(f"Failed to save query to history: {e}")
        
        return SearchResponse(
            query=request.query,
            intent=parsed.get('intent', 'general'),
            entities=parsed.get('entities', {}),
            results=formatted_results,
            total_found=total_count,  # Total count from database, not just returned results
            search_time_ms=search_time
        )
    
    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# RAG endpoint (with LLM generation)
@app.post("/api/rag/query", response_model=RAGResponse)
async def rag_query(
    request: RAGRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """
    RAG query - retrieves relevant requests and generates natural language answer.
    If use_llm=False, returns retrieval only (faster, no model loading needed).
    First query with use_llm=True will load the model (takes 2-5 minutes).
    """
    import time
    start_time = time.time()
    
    try:
        if not rag_service:
            raise HTTPException(status_code=503, detail="RAG service not initialized")
        
        # Execute query with timeout protection
        try:
            result = rag_service.query(
                query=request.query,
                top_k=request.top_k,
                use_llm=request.use_llm
            )
        except Exception as e:
            logger.error(f"RAG query error: {e}", exc_info=True)
            # If LLM query fails, return error but don't crash
            if request.use_llm:
                raise HTTPException(
                    status_code=500,
                    detail=f"LLM generation failed. This might be due to memory issues or model loading problems. Try using 'RAG - רק חיפוש' option instead. Error: {str(e)}"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Retrieval failed: {str(e)}"
                )
        
        # Check if model is loaded
        model_loaded = (
            rag_service.rag_system is not None and
            rag_service.rag_system.model is not None
        ) if request.use_llm else False
        
        response_time = (time.time() - start_time) * 1000
        
        logger.info(f"RAG query: '{request.query}' - {'Generated answer' if request.use_llm else 'Retrieved'} in {response_time:.2f}ms")
        
        # Optional: Save query to history (non-breaking, fails silently if disabled)
        try:
            if os.getenv("ENABLE_QUERY_HISTORY", "false").lower() == "true":
                from scripts.features.query_history.service import QueryHistoryService
                history_service = QueryHistoryService()
                if history_service.is_enabled():
                    # Get user_id from request or use default
                    user_id = getattr(request, 'user_id', 'anonymous')
                    query_type = 'rag-full' if request.use_llm else 'rag-no-llm'
                    history_service.save_query(
                        user_id=user_id,
                        query_text=request.query,
                        query_type=query_type,
                        intent=result.get('intent'),
                        entities=result.get('entities'),
                        result_count=result.get('total_retrieved', 0),
                        execution_time_ms=int(response_time)
                    )
        except Exception as e:
            # Silently fail - don't break RAG if history fails
            logger.debug(f"Failed to save query to history: {e}")
        
        return RAGResponse(
            query=request.query,
            answer=result.get('answer'),
            requests=[{k: v for k, v in req.items() if k != 'embedding'} for req in result.get('requests', [])],
            intent=result.get('intent', 'general'),
            entities=result.get('entities', {}),
            total_retrieved=len(result.get('requests', [])),
            response_time_ms=response_time,
            model_loaded=model_loaded
        )
    
    except Exception as e:
        logger.error(f"RAG query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")


# Get request details
@app.get("/api/requests/{request_id}")
async def get_request_details(
    request_id: str,
    authenticated: bool = Depends(verify_api_key)
):
    """Get full details of a specific request."""
    try:
        if not search_service:
            raise HTTPException(status_code=503, detail="Search service not initialized")
        
        # Query database for full request details
        search_service.cursor.execute(
            "SELECT * FROM requests WHERE requestid = %s",
            (request_id,)
        )
        row = search_service.cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
        
        # Get column names
        column_names = [desc[0] for desc in search_service.cursor.description] if search_service.cursor.description else []
        
        # Build response
        request_data = dict(zip(column_names, row)) if column_names else {}
        
        return {"requestid": request_id, "data": request_data}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get request error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get request: {str(e)}")


# Serve frontend static files (MUST be last - after all API routes)
from fastapi.responses import FileResponse

@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML file."""
    frontend_path = Path(__file__).parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return {"message": "Frontend not found. API is running. Visit /api/health for status."}

@app.get("/{path:path}")
async def serve_static(path: str):
    """Serve static files from frontend directory (catch-all, must be last)."""
    # Skip API routes - they should be handled above
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    frontend_dir = Path(__file__).parent / "frontend"
    file_path = frontend_dir / path
    
    # Security: only serve files from frontend directory
    try:
        file_path.resolve().relative_to(frontend_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    elif path == "" or path.endswith("/"):
        # Serve index.html for directory requests
        index_path = frontend_dir / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
    
    raise HTTPException(status_code=404, detail="File not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

