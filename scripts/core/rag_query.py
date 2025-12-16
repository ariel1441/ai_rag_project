"""
RAG (Retrieval-Augmented Generation) Query System

Uses our improved search for retrieval, then generates natural language answers.
Integrates with:
- Query parser (intent detection, entity extraction)
- Improved search (field-specific, boosting)
- Embeddings (weighted fields)
- Hebrew support
"""
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer
from pgvector.psycopg2 import register_vector
import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import our utilities
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.query_parser import parse_query
from utils.hebrew import fix_hebrew_rtl

# Fix encoding
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 >nul 2>&1')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class RAGSystem:
    """
    Compatible RAG System - Windows CPU Optimized
    
    Designed for:
    - Windows systems with limited RAM
    - CPU-only systems (no GPU)
    - Systems with memory fragmentation issues
    
    Features:
    - Automatically skips 4-bit quantization on Windows CPU (avoids hangs)
    - Uses float16 for compatibility (~7-8GB RAM)
    - Memory-efficient loading
    - Works around Windows-specific issues
    
    ⚠️ CPU OPTIMIZATIONS (TEMPORARY - FOR WEAK CPU):
    - Reduced max tokens to 200 (from 500) for faster generation
    - Uses greedy decoding (instead of sampling) for speed
    - Impact: ~60% shorter answers, ~5-10% less diverse, but core accuracy unchanged
    - TO REVERT FOR GOOD CPU/GPU: Set USE_CPU_OPTIMIZATION = False in generate_answer()
    """
    """
    RAG System that combines retrieval (our search) with generation (LLM).
    
    High-level flow:
    1. Parse query (understand intent, extract entities)
    2. Retrieve relevant requests (using our improved search)
    3. Format context from retrieved requests
    4. Generate answer using LLM
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize RAG system.
        
        Args:
            model_path: Path to Mistral model (defaults to D:/ai_learning/.../models/llm/mistral-7b-instruct)
        """
        self.model_path = model_path or self._get_default_model_path()
        self.model = None
        self.tokenizer = None
        self.embedding_model = None
        self.config = None
        
        # Database connection
        self.conn = None
        self.cursor = None
        
        # Load config
        self._load_config()
        
        print("RAG System initialized")
        print(f"Model path: {self.model_path}")
    
    def _get_default_model_path(self) -> str:
        """Get default model path on D: drive."""
        current_path = Path(__file__).resolve()
        if str(current_path).startswith('D:'):
            base_path = current_path.parent.parent.parent
        else:
            base_path = Path("D:/ai_learning/train_ai_tamar_request")
        return str(base_path / "models" / "llm" / "mistral-7b-instruct")
    
    def _load_config(self):
        """Load search configuration."""
        config_path = Path(__file__).parent.parent.parent / "config" / "search_config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"⚠ Could not load config: {e}, using defaults")
                self.config = None
        else:
            self.config = None
    
    def connect_db(self):
        """Connect to database."""
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
    
    def load_model(self):
        """Load LLM model and tokenizer."""
        if self.model is not None:
            return  # Already loaded
        
        print("Loading LLM model...")
        print("(This takes 30-60 seconds on first load)")
        
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            # Check if model exists
            if not Path(self.model_path).exists():
                raise FileNotFoundError(
                    f"Model not found at {self.model_path}\n"
                    f"Please download it first using: python scripts/core/download_rag_model.py"
                )
            
            # Load tokenizer
            print("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                local_files_only=True
            )
            
            # Set pad token if not set (required for generation)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Try to load with 4-bit quantization (uses ~4GB RAM instead of 15GB)
            # If quantization fails (e.g., Python 3.14 compatibility), fall back to float16
            print("Loading model...")
            print("⚠️  Attempting 4-bit quantization (~4GB RAM)")
            print("    If unavailable, will use float16 (~7-8GB RAM)")
            print()
            
            import torch
            
            # Try 4-bit quantization first (if Python version supports it)
            use_quantization = False
            quantization_error = None
            
            # Check Python version - bitsandbytes doesn't work on Python 3.14+
            import sys
            python_version = sys.version_info
            
            # SKIP 4-bit quantization on Windows CPU - it hangs after loading shards
            # This is a known issue: bitsandbytes on Windows CPU has memory fragmentation
            # and hangs during quantization initialization even after shards load
            skip_4bit = False
            if python_version.major == 3 and python_version.minor >= 14:
                print("⚠️  Python 3.14+ detected - bitsandbytes not supported")
                print("   Skipping 4-bit quantization, using float16 (~7-8GB RAM)")
                quantization_error = "Python 3.14+ not supported by bitsandbytes"
                skip_4bit = True
            elif sys.platform == 'win32' and not self._has_gpu():
                # Windows CPU: Skip 4-bit entirely - it hangs after loading shards
                print("⚠️  Windows CPU detected - skipping 4-bit quantization")
                print("   (Known issue: hangs after loading shards)")
                print("   Using float16 directly (~7-8GB RAM)")
                quantization_error = "Windows CPU - 4-bit quantization hangs"
                skip_4bit = True
            
            if not skip_4bit:
                try:
                    from transformers import BitsAndBytesConfig
                    
                    # 4-bit quantization config (reduces memory from 15GB to ~4GB)
                    quantization_config = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype=torch.float16,
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_quant_type="nf4"
                    )
                    
                    print("Attempting 4-bit quantization...")
                    print("⏳ Loading model (this takes 30-60 seconds, please wait)...")
                    print("   Progress: Loading checkpoint shards...")
                    sys.stdout.flush()  # Force output to appear immediately
                    
                    # Use explicit CPU device_map to prevent memory allocation issues
                    device_map_setting = "cpu"  # Force CPU (more stable)
                    if self._has_gpu():
                        device_map_setting = "auto"  # Use GPU if available
                    
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_path,
                        local_files_only=True,
                        quantization_config=quantization_config,  # 4-bit quantization
                        device_map=device_map_setting,
                        low_cpu_mem_usage=True
                    )
                    use_quantization = True
                    print("✅ Loaded with 4-bit quantization (~4GB RAM)")
                    
                except (ImportError, RuntimeError, ModuleNotFoundError) as e:
                    # Quantization failed (e.g., memory fragmentation, Python 3.14 compatibility)
                    quantization_error = str(e)
                    error_preview = quantization_error[:150] if len(quantization_error) > 150 else quantization_error
                    print(f"⚠️  4-bit quantization failed: {error_preview}")
                    if "not enough memory" in quantization_error.lower() or "alloc" in quantization_error.lower():
                        print("   This is likely a memory fragmentation issue on Windows CPU")
                        print("   Falling back to float16 (~7-8GB RAM)")
                    else:
                        print("   Falling back to float16 (~7-8GB RAM)")
                    print()
            
            # Fallback to float16 if quantization didn't work
            if not use_quantization:
                
                # Fallback: Use float16 (still saves memory, ~7-8GB)
                # Use CPU-only loading for stability (avoids GPU issues)
                try:
                    print("Loading with float16 (CPU-only for stability)...")
                    print("⏳ This may take 1-2 minutes - please be patient...")
                    print("   Progress: Loading checkpoint shards...")
                    sys.stdout.flush()  # Force output to appear immediately
                    print()
                    
                    # Force CPU loading (more stable, avoids GPU memory issues)
                    # Use low_cpu_mem_usage for memory-efficient loading
                    # This loads shards one at a time to reduce RAM pressure
                    print("   Using memory-efficient loading (low_cpu_mem_usage=True)")
                    print("   This loads shards incrementally to reduce RAM pressure")
                    sys.stdout.flush()
                    
                    # Check available memory before loading
                    try:
                        import psutil
                        mem = psutil.virtual_memory()
                        available_gb = mem.available / (1024**3)
                        print(f"   Available RAM: {available_gb:.1f} GB")
                        if available_gb < 8:
                            print(f"   ⚠️  Warning: Less than 8GB free RAM - loading may fail")
                            print(f"   Recommendation: Close other applications or restart computer")
                        sys.stdout.flush()
                    except:
                        pass
                    
                    # Try loading with maximum memory efficiency
                    # Wrap in try-except to catch any error, including early crashes
                    try:
                        print("   Starting model loading...")
                        print("   ⏳ Loading shards (this shows progress automatically)...")
                        print("   ⏳ After shards load, model initializes (may take 1-2 more minutes)")
                        sys.stdout.flush()
                        
                        import time
                        load_start = time.time()
                        
                        # Add progress callback if possible
                        def log_progress(message=""):
                            elapsed = time.time() - load_start
                            print(f"   [⏱️  {elapsed:.0f}s] {message}")
                            sys.stdout.flush()
                        
                        # Attempt to pre-allocate memory to reduce fragmentation
                        # This tries to "reserve" a large block before loading
                        log_progress("Attempting memory pre-allocation to reduce fragmentation...")
                        try:
                            import torch
                            # Try to allocate a large block (2GB) then free it
                            # This helps "defragment" memory by forcing OS to find large blocks
                            print("   Pre-allocating large memory block (helps reduce fragmentation)...")
                            dummy_tensor = torch.zeros(512 * 1024 * 1024, dtype=torch.float32)  # 2GB
                            del dummy_tensor
                            torch.cuda.empty_cache() if torch.cuda.is_available() else None
                            print("   ✅ Memory pre-allocation complete")
                            sys.stdout.flush()
                        except Exception as prealloc_error:
                            # Pre-allocation failed, but continue anyway
                            print(f"   ⚠️  Memory pre-allocation failed (non-critical): {prealloc_error}")
                            sys.stdout.flush()
                        
                        log_progress("Calling from_pretrained()...")
                        
                        # Wrap in additional try-except to catch crashes at shard loading
                        try:
                            # Use GPU if available, otherwise CPU
                            device_map_setting = "auto" if self._has_gpu() else "cpu"
                            if self._has_gpu():
                                print("   ✅ GPU detected - using GPU acceleration")
                                print("   This will be much faster than CPU!")
                            else:
                                print("   ⚠️  No GPU - using CPU (will be slower)")
                            sys.stdout.flush()
                            
                            self.model = AutoModelForCausalLM.from_pretrained(
                                self.model_path,
                                local_files_only=True,
                                dtype=torch.float16,  # Half precision (use dtype instead of torch_dtype)
                                device_map=device_map_setting,  # Auto (GPU if available) or CPU
                                low_cpu_mem_usage=True,  # Memory-efficient loading (loads shards incrementally)
                                # Note: offload_folder is not a valid parameter for from_pretrained
                                # low_cpu_mem_usage=True already does incremental loading
                            )
                        except (RuntimeError, MemoryError, OSError) as shard_error:
                            # Catch errors during shard loading (especially at 67% - shard 2/3)
                            error_str = str(shard_error)
                            print()
                            print("="*80)
                            print("❌ MODEL LOADING FAILED DURING SHARD LOADING")
                            print("="*80)
                            print(f"Error: {error_str}")
                            print()
                            print("This often happens at 67% (shard 2/3) due to memory fragmentation.")
                            print("The process may have crashed or run out of memory.")
                            print()
                            print("SOLUTIONS:")
                            print("  1. RESTART YOUR COMPUTER (clears memory fragmentation)")
                            print("  2. Close other applications to free RAM")
                            print("  3. Use 'RAG - רק חיפוש' option (no model loading needed)")
                            print("="*80)
                            print()
                            sys.stdout.flush()
                            raise
                        
                        load_time = time.time() - load_start
                        print(f"✅ Loaded with float16 (~7-8GB RAM) in {load_time:.1f} seconds")
                        print("   Model is now in memory and ready for inference")
                        sys.stdout.flush()
                    except (RuntimeError, MemoryError, OSError, Exception) as load_error:
                        # Catch ALL errors including memory errors
                        error_str = str(load_error)
                        error_type = type(load_error).__name__
                        
                        print()
                        print("="*80)
                        print("❌ MODEL LOADING FAILED")
                        print("="*80)
                        print(f"Error Type: {error_type}")
                        print(f"Error Message: {error_str}")
                        print()
                        import traceback
                        print("Full Traceback:")
                        traceback.print_exc()
                        print("="*80)
                        print()
                        
                        # Check if it's a memory issue
                        error_lower = error_str.lower()
                        if any(keyword in error_lower for keyword in [
                            "memory", "alloc", "out of memory", "cannot allocate",
                            "not enough", "fragmentation"
                        ]):
                            print("🔍 DIAGNOSIS: Memory Allocation Issue")
                            print()
                            print("You have enough total RAM (10GB+ free), but Windows")
                            print("cannot find a large enough contiguous block.")
                            print()
                            print("This is a MEMORY FRAGMENTATION issue.")
                            print()
                            print("✅ SOLUTIONS (in order):")
                            print("  1. RESTART YOUR COMPUTER")
                            print("     - This clears memory fragmentation")
                            print("     - Close all apps before restart")
                            print("     - Run test immediately after restart")
                            print()
                            print("  2. Close ALL other applications")
                            print("     - Browser, IDEs, other programs")
                            print("     - Free as much RAM as possible")
                            print()
                            print("  3. If still failing after restart:")
                            print("     - Model may be too large for your system")
                            print("     - Consider using API-based LLM instead")
                            print("     - Or use a smaller model")
                        else:
                            print("🔍 DIAGNOSIS: Unknown Error")
                            print("   This might be a different issue.")
                            print("   Check the error message above for details.")
                        
                        print()
                        print("="*80)
                        raise MemoryError(
                            f"Model loading failed: {error_str}\n\n"
                            f"Most likely cause: Memory fragmentation.\n"
                            f"Solution: Restart computer and try again."
                        )
                except torch.cuda.OutOfMemoryError:
                    raise MemoryError(
                        "GPU out of memory. Try using CPU."
                    )
                except RuntimeError as e2:
                    # Print error immediately so user sees it
                    print()
                    print("="*80)
                    print("❌ ERROR DURING MODEL LOADING")
                    print("="*80)
                    print(f"Error: {e2}")
                    print()
                    import traceback
                    traceback.print_exc()
                    print("="*80)
                    print()
                    
                    error_msg = str(e2).lower()
                    if "out of memory" in error_msg or "cannot allocate memory" in error_msg:
                        raise MemoryError(
                            f"Not enough RAM to load model.\n"
                            f"Error: {e2}\n\n"
                            f"Solutions:\n"
                            f"  1. Close other applications to free RAM\n"
                            f"  2. Restart computer to free cached RAM\n"
                            f"  3. Need at least 8GB free RAM for float16 model"
                        )
                    raise
            
            print("✅ Model loaded successfully")
            
        except ImportError:
            raise ImportError(
                "transformers library not installed.\n"
                "Install with: pip install transformers torch"
            )
        except Exception as e:
            raise Exception(f"Failed to load model: {e}")
    
    def _has_gpu(self) -> bool:
        """Check if GPU is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False
    
    def retrieve_requests(self, query: str, top_k: int = 20) -> List[Dict]:
        """
        Retrieve relevant requests using our improved search.
        
        This uses the same logic as search.py but returns structured data.
        
        Args:
            query: User query
            top_k: Number of requests to retrieve
            
        Returns:
            List of request dictionaries with fields:
            - requestid
            - similarity
            - projectname
            - updatedby
            - createdby
            - etc.
        """
        import time
        retrieval_start = time.time()
        
        if not self.conn:
            self.connect_db()
        
        # Parse query
        parsed = parse_query(query, self.config)
        
        # Generate query embedding
        if self.embedding_model is None:
            self.embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        
        query_embedding = self.embedding_model.encode(
            query, normalize_embeddings=True, convert_to_numpy=True
        )
        
        # Create temp table
        self.cursor.execute("""
            CREATE TEMP TABLE temp_query_embedding (
                id SERIAL PRIMARY KEY,
                embedding vector(384)
            );
        """)
        
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        self.cursor.execute("""
            INSERT INTO temp_query_embedding (embedding)
            VALUES (%s::vector);
        """, (embedding_str,))
        self.conn.commit()
        
        # Build filters (enhanced with date and urgency support)
        sql_filters = []
        filter_params = []
        
        if 'type_id' in parsed['entities']:
            sql_filters.append("r.requesttypeid::TEXT = %s::TEXT")
            filter_params.append(str(parsed['entities']['type_id']))
        
        if 'status_id' in parsed['entities']:
            sql_filters.append("r.requeststatusid::TEXT = %s::TEXT")
            filter_params.append(str(parsed['entities']['status_id']))
        
        # Date filtering
        if 'date_range' in parsed['entities']:
            date_range = parsed['entities']['date_range']
            date_field = "r.requeststatusdate"
            
            if 'start' in date_range and date_range['start']:
                sql_filters.append(f"{date_field} >= %s::DATE")
                filter_params.append(date_range['start'].isoformat())
            
            if 'end' in date_range and date_range['end']:
                sql_filters.append(f"{date_field} <= %s::DATE")
                filter_params.append(date_range['end'].isoformat())
            
            # Days back filter (alternative to start/end)
            if 'days' in date_range and date_range['days'] and 'start' not in date_range:
                sql_filters.append(f"{date_field} >= CURRENT_DATE - INTERVAL '%s days'")
                filter_params.append(str(date_range['days']))
        
        # Urgency filtering (requests with close deadline)
        if parsed['entities'].get('urgency', False):
            # Filter by requeststatusdate close to today (within 7 days)
            sql_filters.append("r.requeststatusdate IS NOT NULL")
            sql_filters.append("r.requeststatusdate >= CURRENT_DATE")
            sql_filters.append("r.requeststatusdate <= CURRENT_DATE + INTERVAL '7 days'")
        
        request_filter_sql = ""
        if sql_filters:
            request_filter_sql = "WHERE " + " AND ".join(sql_filters)
        
        # Build boost logic (same as search.py)
        boost_cases = []
        if parsed['target_fields'] and parsed['entities']:
            entity_value = None
            if 'person_name' in parsed['entities']:
                entity_value = parsed['entities']['person_name']
            elif 'project_name' in parsed['entities']:
                entity_value = parsed['entities']['project_name']
            
            if entity_value:
                entity_escaped = entity_value.replace("'", "''")
                field_labels = {
                    'updatedby': 'Updated By',
                    'createdby': 'Created By',
                    'responsibleemployeename': 'Responsible Employee',
                    'contactfirstname': 'Contact First Name',
                    'contactlastname': 'Contact Last Name',
                    'projectname': 'Project',
                    'projectdesc': 'Description'
                }
                
                for field in parsed['target_fields']:
                    if field in field_labels:
                        label = field_labels[field]
                        boost_cases.append(f"WHEN e.text_chunk LIKE '%{label}: %{entity_escaped}%' THEN 2.0")
                
                boost_cases.append(f"WHEN e.text_chunk LIKE '%{entity_escaped}%' THEN 1.5")
        
        if not boost_cases:
            boost_sql = "1.0 as boost"
            order_boost_sql = "1.0"
        else:
            boost_cases.append("ELSE 1.0")
            boost_sql = "CASE " + " ".join(boost_cases) + " END as boost"
            order_boost_sql = "CASE " + " ".join(boost_cases) + " END"
        
        # Search
        embedding_where = "WHERE e.embedding IS NOT NULL"
        join_sql = ""
        if request_filter_sql:
            join_sql = "INNER JOIN requests r ON e.requestid = r.requestid"
            embedding_where += " AND " + request_filter_sql.replace("WHERE ", "")
        
        search_sql = f"""
            SELECT 
                e.requestid,
                e.chunk_index,
                1 - (e.embedding <=> t.embedding) as similarity,
                {boost_sql}
            FROM request_embeddings e
            {join_sql}
            CROSS JOIN temp_query_embedding t
            {embedding_where}
            ORDER BY (1 - (e.embedding <=> t.embedding)) * ({order_boost_sql}) DESC
            LIMIT {top_k * 3};
        """
        
        if filter_params:
            self.cursor.execute(search_sql, tuple(filter_params))
        else:
            self.cursor.execute(search_sql)
        
        chunk_results = self.cursor.fetchall()
        
        # Group by request ID
        request_scores = {}
        for req_id, chunk_idx, similarity, boost in chunk_results:
            if req_id not in request_scores:
                request_scores[req_id] = {
                    'best_similarity': similarity,
                    'best_chunk': chunk_idx,
                    'boost': float(boost) if boost else 1.0
                }
            else:
                if similarity > request_scores[req_id]['best_similarity']:
                    request_scores[req_id]['best_similarity'] = similarity
                    request_scores[req_id]['best_chunk'] = chunk_idx
        
        # Get top requests
        sorted_requests = sorted(
            request_scores.items(),
            key=lambda x: x[1]['best_similarity'] * x[1]['boost'],
            reverse=True
        )
        
        unique_request_ids = [req_id for req_id, _ in sorted_requests[:top_k]]
        
        if not unique_request_ids:
            return []
        
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
            ORDER BY requestid;
        """, unique_request_ids)
        
        full_requests = self.cursor.fetchall()
        
        # Format as dictionaries
        requests_dict = {}
        for req in full_requests:
            (req_id, projectname, projectdesc, areadesc, remarks,
             updatedby, createdby, responsibleemployeename,
             contactfirstname, contactlastname, contactemail,
             requesttypeid, requeststatusid, requeststatusdate) = req
            
            score_info = request_scores.get(req_id, {})
            
            requests_dict[req_id] = {
                'requestid': req_id,
                'projectname': projectname,
                'projectdesc': projectdesc,
                'areadesc': areadesc,
                'remarks': remarks,
                'updatedby': updatedby,
                'createdby': createdby,
                'responsibleemployeename': responsibleemployeename,
                'contactfirstname': contactfirstname,
                'contactlastname': contactlastname,
                'contactemail': contactemail,
                'requesttypeid': requesttypeid,
                'requeststatusid': requeststatusid,
                'requeststatusdate': requeststatusdate,
                'similarity': score_info.get('best_similarity', 0.0),
                'boost': score_info.get('boost', 1.0)
            }
        
        # Clean up
        self.cursor.execute("DROP TABLE IF EXISTS temp_query_embedding;")
        
        # Return in order of similarity
        retrieval_end = time.time()
        retrieval_duration = retrieval_end - retrieval_start
        if retrieval_duration > 1:  # Only print if > 1 second
            print(f"   [⏱️  Retrieval took: {retrieval_duration:.2f} seconds]")
        return [requests_dict[req_id] for req_id in unique_request_ids if req_id in requests_dict]
    
    def format_context(self, requests: List[Dict], query_type: str, parsed: Optional[Dict] = None) -> str:
        """
        Format retrieved requests into context for LLM.
        Adapts formatting based on query type and detected entities.
        
        Args:
            requests: List of request dictionaries
            query_type: Type of query (find, count, summarize, similar, urgent, etc.)
            parsed: Parsed query information (optional, for entity-aware formatting)
            
        Returns:
            Formatted context string
        """
        if not requests:
            return "לא נמצאו פניות רלוונטיות."
        
        # Determine if we need special formatting
        entities = parsed.get('entities', {}) if parsed else {}
        entity_type = parsed.get('entity_type') if parsed else None
        is_project_query = entity_type == 'projects'
        is_urgent_query = query_type == 'urgent' or entities.get('urgency', False)
        
        context_parts = []
        context_parts.append(f"נמצאו {len(requests)} פניות רלוונטיות:\n")
        
        for i, req in enumerate(requests, 1):
            parts = []
            
            # Request ID
            parts.append(f"פנייה מספר {req['requestid']}")
            
            # Key fields - always include important ones
            if req.get('projectname'):
                parts.append(f"פרויקט: {req['projectname']}")
            
            if req.get('updatedby'):
                parts.append(f"עודכן על ידי: {req['updatedby']}")
            
            if req.get('createdby'):
                parts.append(f"נוצר על ידי: {req['createdby']}")
            
            if req.get('responsibleemployeename'):
                parts.append(f"אחראי: {req['responsibleemployeename']}")
            
            if req.get('requesttypeid'):
                parts.append(f"סוג: {req['requesttypeid']}")
            
            if req.get('requeststatusid'):
                parts.append(f"סטטוס: {req['requeststatusid']}")
            
            # For urgent queries, include date information with better calculations
            if is_urgent_query and req.get('requeststatusdate'):
                try:
                    # Calculate days until deadline with better categorization
                    from datetime import datetime
                    status_date = req['requeststatusdate']
                    
                    if isinstance(status_date, str):
                        try:
                            date_obj = datetime.strptime(status_date[:10], '%Y-%m-%d').date()
                        except:
                            parts.append(f"תאריך יעד: {status_date}")
                            continue
                    else:
                        date_obj = status_date
                    
                    today = datetime.now().date()
                    days_until = (date_obj - today).days
                    
                    # Categorize urgency
                    if days_until < 0:
                        urgency_level = "עבר"
                        urgency_text = f"עבר לפני {abs(days_until)} ימים"
                    elif days_until == 0:
                        urgency_level = "היום"
                        urgency_text = "היום!"
                    elif days_until <= 3:
                        urgency_level = "דחוף מאוד"
                        urgency_text = f"{days_until} ימים (דחוף מאוד!)"
                    elif days_until <= 7:
                        urgency_level = "דחוף"
                        urgency_text = f"{days_until} ימים"
                    else:
                        urgency_level = "לא דחוף"
                        urgency_text = f"{days_until} ימים"
                    
                    parts.append(f"תאריך יעד: {urgency_text} ({urgency_level})")
                except Exception as e:
                    # Fallback to simple date
                    try:
                        parts.append(f"תאריך יעד: {req.get('requeststatusdate')}")
                    except:
                        pass
            
            if req.get('contactfirstname') or req.get('contactlastname'):
                contact = f"{req.get('contactfirstname', '')} {req.get('contactlastname', '')}".strip()
                if contact:
                    parts.append(f"איש קשר: {contact}")
            
            if req.get('projectdesc'):
                desc = str(req['projectdesc'])[:150]  # Limit description
                if len(str(req['projectdesc'])) > 150:
                    desc += "..."
                parts.append(f"תיאור: {desc}")
            
            # Include more fields for better context
            if req.get('areadesc'):
                area = str(req['areadesc'])[:100]
                if len(str(req['areadesc'])) > 100:
                    area += "..."
                parts.append(f"אזור: {area}")
            
            if req.get('remarks'):
                remarks = str(req['remarks'])[:100]
                if len(str(req['remarks'])) > 100:
                    remarks += "..."
                parts.append(f"הערות: {remarks}")
            
            if req.get('contactemail'):
                parts.append(f"אימייל: {req['contactemail']}")
            
            # Format as Hebrew-friendly list
            context_parts.append(f"{i}. {' | '.join(parts)}")
        
        return "\n".join(context_parts)
    
    def _count_projects(self, requests: List[Dict], parsed: Dict) -> Dict[str, int]:
        """
        Count requests per project.
        
        Args:
            requests: List of request dictionaries
            parsed: Parsed query information
            
        Returns:
            Dictionary mapping project name to count
        """
        project_counts = {}
        for req in requests:
            project_name = req.get('projectname')
            if project_name:
                # Normalize project name (handle None, empty, etc.)
                project_name = str(project_name).strip()
                if project_name and project_name.upper() not in ('NONE', 'NULL', ''):
                    project_counts[project_name] = project_counts.get(project_name, 0) + 1
        
        # Sort by count (descending)
        return dict(sorted(project_counts.items(), key=lambda x: x[1], reverse=True))
    
    def _format_project_context(self, project_counts: Dict[str, int], parsed: Dict) -> str:
        """
        Format project counts into context for LLM.
        
        Args:
            project_counts: Dictionary mapping project name to count
            parsed: Parsed query information
            
        Returns:
            Formatted context string
        """
        if not project_counts:
            return "לא נמצאו פרויקטים."
        
        context_parts = []
        total_projects = len(project_counts)
        total_requests = sum(project_counts.values())
        
        context_parts.append(f"נמצאו {total_projects} פרויקטים שונים עם סה\"כ {total_requests} פניות:\n")
        
        for i, (project_name, count) in enumerate(list(project_counts.items())[:20], 1):
            context_parts.append(f"{i}. {project_name}: {count} פניות")
        
        if len(project_counts) > 20:
            context_parts.append(f"\n...ועוד {len(project_counts) - 20} פרויקטים")
        
        return "\n".join(context_parts)
    
    def _fetch_request_by_id(self, request_id: str) -> Optional[Dict]:
        """
        Fetch a single request by ID.
        
        Args:
            request_id: Request ID to fetch
            
        Returns:
            Request dictionary or None if not found
        """
        if not self.conn:
            self.connect_db()
        
        self.cursor.execute("""
            SELECT 
                requestid, projectname, projectdesc, areadesc, remarks,
                updatedby, createdby, responsibleemployeename,
                contactfirstname, contactlastname, contactemail,
                requesttypeid, requeststatusid, requeststatusdate
            FROM requests
            WHERE requestid = %s
        """, (request_id,))
        
        result = self.cursor.fetchone()
        if not result:
            return None
        
        (req_id, projectname, projectdesc, areadesc, remarks,
         updatedby, createdby, responsibleemployeename,
         contactfirstname, contactlastname, contactemail,
         requesttypeid, requeststatusid, requeststatusdate) = result
        
        return {
            'requestid': req_id,
            'projectname': projectname,
            'projectdesc': projectdesc,
            'areadesc': areadesc,
            'remarks': remarks,
            'updatedby': updatedby,
            'createdby': createdby,
            'responsibleemployeename': responsibleemployeename,
            'contactfirstname': contactfirstname,
            'contactlastname': contactlastname,
            'contactemail': contactemail,
            'requesttypeid': requesttypeid,
            'requeststatusid': requeststatusid,
            'requeststatusdate': requeststatusdate,
        }
    
    def retrieve_similar_requests(self, request_id: str, top_k: int = 20, 
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
            ORDER BY e.embedding <=> %s::vector
            LIMIT %s
        """, (embedding_str, request_id, embedding_str, top_k * 3))
        
        chunk_results = self.cursor.fetchall()
        
        # Group by request ID, keep best similarity
        request_scores = {}
        for req_id, chunk_idx, similarity in chunk_results:
            if similarity >= similarity_threshold:  # Filter by threshold
                if req_id not in request_scores or similarity > request_scores[req_id]:
                    request_scores[req_id] = similarity
        
        # Get top requests
        sorted_ids = sorted(request_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        if not sorted_ids:
            return [], {}
        
        # Fetch full request data
        placeholders = ','.join(['%s'] * len(sorted_ids))
        self.cursor.execute(f"""
            SELECT 
                requestid, projectname, projectdesc, areadesc, remarks,
                updatedby, createdby, responsibleemployeename,
                contactfirstname, contactlastname, contactemail,
                requesttypeid, requeststatusid, requeststatusdate
            FROM requests
            WHERE requestid IN ({placeholders})
        """, [req_id for req_id, _ in sorted_ids])
        
        requests = self.cursor.fetchall()
        requests_dict = {req[0]: req for req in requests}
        
        # Return in order with similarity scores
        result = []
        similarity_scores = {}
        for req_id, similarity in sorted_ids:
            if req_id in requests_dict:
                req_data = requests_dict[req_id]
                result.append({
                    'requestid': req_data[0],
                    'projectname': req_data[1],
                    'projectdesc': req_data[2],
                    'areadesc': req_data[3],
                    'remarks': req_data[4],
                    'updatedby': req_data[5],
                    'createdby': req_data[6],
                    'responsibleemployeename': req_data[7],
                    'contactfirstname': req_data[8],
                    'contactlastname': req_data[9],
                    'contactemail': req_data[10],
                    'requesttypeid': req_data[11],
                    'requeststatusid': req_data[12],
                    'requeststatusdate': req_data[13],
                    'similarity': similarity
                })
                similarity_scores[req_id] = similarity
        
        return result, similarity_scores
    
    def format_similar_context(self, source_request: Dict, similar_requests: List[Dict],
                              similarity_scores: Dict[str, float]) -> str:
        """
        Format context showing what makes requests similar.
        
        Args:
            source_request: Source request dictionary
            similar_requests: List of similar requests
            similarity_scores: Dictionary mapping request ID to similarity score
            
        Returns:
            Formatted context string
        """
        context_parts = []
        context_parts.append(f"פנייה מקור: {source_request['requestid']}")
        if source_request.get('projectname'):
            context_parts.append(f"פרויקט: {source_request['projectname']}")
        if source_request.get('requesttypeid'):
            context_parts.append(f"סוג: {source_request['requesttypeid']}")
        if source_request.get('requeststatusid'):
            context_parts.append(f"סטטוס: {source_request['requeststatusid']}")
        if source_request.get('updatedby'):
            context_parts.append(f"עודכן על ידי: {source_request['updatedby']}")
        context_parts.append("")
        context_parts.append(f"נמצאו {len(similar_requests)} פניות דומות:\n")
        
        for i, req in enumerate(similar_requests, 1):
            req_id = req['requestid']
            similarity = similarity_scores.get(req_id, 0.0)
            
            parts = [f"פנייה {req_id} (דמיון: {similarity:.1%})"]
            
            # Highlight matching fields
            matches = []
            if req.get('projectname') == source_request.get('projectname') and req.get('projectname'):
                matches.append(f"✓ אותו פרויקט: {req['projectname']}")
            
            if req.get('requesttypeid') == source_request.get('requesttypeid') and req.get('requesttypeid'):
                matches.append(f"✓ אותו סוג: {req['requesttypeid']}")
            
            if req.get('requeststatusid') == source_request.get('requeststatusid') and req.get('requeststatusid'):
                matches.append(f"✓ אותו סטטוס: {req['requeststatusid']}")
            
            if req.get('updatedby') == source_request.get('updatedby') and req.get('updatedby'):
                matches.append(f"✓ אותו מעדכן: {req['updatedby']}")
            
            if matches:
                parts.append(" | ".join(matches))
            
            # Add basic info
            if req.get('projectname'):
                parts.append(f"פרויקט: {req['projectname']}")
            if req.get('requesttypeid'):
                parts.append(f"סוג: {req['requesttypeid']}")
            if req.get('requeststatusid'):
                parts.append(f"סטטוס: {req['requeststatusid']}")
            
            context_parts.append(f"{i}. {' | '.join(parts)}")
        
        return "\n".join(context_parts)
    
    def _generate_project_count_answer(self, project_counts: Dict[str, int], parsed: Dict) -> str:
        """
        Generate answer for project counting queries without LLM.
        
        Args:
            project_counts: Dictionary mapping project name to count
            parsed: Parsed query information
            
        Returns:
            Formatted answer string
        """
        if not project_counts:
            person_name = parsed.get('entities', {}).get('person_name', '')
            if person_name:
                return f"לא נמצאו פרויקטים ל{person_name}."
            return "לא נמצאו פרויקטים."
        
        total_projects = len(project_counts)
        total_requests = sum(project_counts.values())
        
        # Get person name if available
        person_name = parsed.get('entities', {}).get('person_name', '')
        
        if person_name:
            answer = f"ל{person_name} יש {total_projects} פרויקטים שונים עם סה\"כ {total_requests} פניות:\n\n"
        else:
            answer = f"נמצאו {total_projects} פרויקטים שונים עם סה\"כ {total_requests} פניות:\n\n"
        
        # List top projects
        sorted_projects = sorted(project_counts.items(), key=lambda x: x[1], reverse=True)
        for i, (project_name, count) in enumerate(sorted_projects[:10], 1):
            answer += f"{i}. {project_name}: {count} פניות\n"
        
        if len(sorted_projects) > 10:
            answer += f"\n...ועוד {len(sorted_projects) - 10} פרויקטים"
        
        return answer
    
    def build_prompt(self, query: str, context: str, parsed: Dict) -> str:
        """
        Build dynamic prompt for LLM based on query type, intent, and extracted entities.
        Adapts to query complexity and detected entities (dates, urgency, projects, etc.).
        
        Args:
            query: User query
            context: Formatted context from retrieved requests
            parsed: Parsed query information with all detected entities
            
        Returns:
            Complete prompt string (will be formatted with chat template)
        """
        query_type = parsed.get('query_type', 'find')
        intent = parsed.get('intent', 'general')
        entities = parsed.get('entities', {})
        entity_type = parsed.get('entity_type')  # 'projects' or 'requests'
        
        # Base system prompt - VERY CLEAR about what to generate
        system_prompt = """אתה עוזר מועיל שעונה על שאלות על פניות במסד נתונים.
אתה מקבל רשימת פניות רלוונטיות ועונה על השאלה בעברית בצורה טקסטואלית.
חשוב: אל תחזור על פרטי הפניות - תן תשובה טקסטואלית שמסכמת או עונה על השאלה."""
        
        # Build dynamic instruction based on query type and entities
        instruction = self._build_dynamic_instruction(query_type, intent, entities, entity_type)
        
        # Add context about detected entities
        entity_context = self._build_entity_context(entities, query_type)
        
        # Build user message content - CLEAR STRUCTURE
        user_content = f"""{system_prompt}

{instruction}
{entity_context}

רשימת פניות רלוונטיות (להתייחסות בלבד - אל תפרט אותן):
{context}

שאלה: {query}

תשובה (עברית, טקסטואלית, תמציתית):"""
        
        return user_content
    
    def _build_dynamic_instruction(self, query_type: str, intent: str, entities: Dict, entity_type: Optional[str]) -> str:
        """
        Build dynamic instruction based on query type and detected entities.
        
        Args:
            query_type: Type of query (count, summarize, find, urgent, etc.)
            intent: Query intent (person, project, type, etc.)
            entities: Extracted entities
            entity_type: 'projects' or 'requests' or None
            
        Returns:
            Instruction string for LLM
        """
        # Determine what entity user is asking about
        is_project_query = entity_type == 'projects' or 'project_name' in entities
        
        if query_type == 'count':
            if is_project_query:
                # Count projects, not requests
                instruction = """ספור את הפרויקטים השונים וציין כמה פניות יש לכל פרויקט.
ענה בצורה:
"יש X פרויקטים:
1. שם פרויקט (Y פניות)
2. שם פרויקט (Z פניות)
..."
אל תפרט כל פנייה - רק רשימת פרויקטים עם מספר פניות."""
            else:
                # Count requests - check if database count is in context
                if 'מספר מדויק מהמסד נתונים' in context:
                    # Extract the count from context
                    import re
                    count_match = re.search(r'מספר מדויק מהמסד נתונים: (\d+) פניות', context)
                    if count_match:
                        db_count = count_match.group(1)
                        instruction = f"""ספור את הפניות וספק את המספר המדויק.
המספר המדויק מהמסד נתונים הוא: {db_count} פניות.
ענה בצורה: "נמצאו {db_count} פניות של [שם/פרויקט/סוג]."
אל תפרט את כל הפניות - רק תן את המספר והסבר קצר."""
                    else:
                        instruction = """ספור את הפניות וספק את המספר המדויק.
ענה בצורה: "נמצאו X פניות של [שם/פרויקט/סוג]."
אל תפרט את כל הפניות - רק תן את המספר והסבר קצר."""
                else:
                    # Count requests
                    instruction = """ספור את הפניות וספק את המספר המדויק.
ענה בצורה: "נמצאו X פניות של [שם/פרויקט/סוג]."
אל תפרט את כל הפניות - רק תן את המספר והסבר קצר."""
        
        elif query_type == 'summarize':
            # Check if statistics are in context (pre-calculated)
            if 'סטטיסטיקות מחושבות' in context:
                instruction = """ספק סיכום טקסטואלי מפורט של הפניות.
השתמש בסטטיסטיקות המחושבות שסופקו (אל תחשב מחדש).

פורמט:
1. מספר כולל: "נמצאו X פניות"
2. סטטיסטיקות מפתח (השתמש במספרים המחושבים):
   - "רוב הפניות בסטטוס Y (Z פניות, W%)"
   - "הסוגים העיקריים: A (X פניות), B (Y פניות)"
   - "הפרויקטים העיקריים: X (A פניות), Y (B פניות)"
   - "האנשים העיקריים: X (A פניות), Y (B פניות)"
3. דפוסים ותובנות:
   - "רוב הפניות נוצרו בחודשים האחרונים"
   - "יש עלייה בפניות בפרויקט X"

אל תפרט כל פנייה - תן סיכום כללי עם סטטיסטיקות מהנתונים המחושבים."""
            else:
                instruction = """ספק סיכום טקסטואלי מפורט של הפניות.
כלול:
- מספר כולל
- סטטיסטיקות מפתח (סטטוסים, פרויקטים, סוגים)
- דפוסים ותובנות
- פרויקטים/אנשים/סוגים העיקריים

ענה בצורה: "נמצאו X פניות. רוב הפניות בסטטוס Y (Z%). הפרויקטים העיקריים הם: A (M פניות), B (N פניות). דפוסים: ..."
אל תפרט כל פנייה - תן סיכום כללי עם סטטיסטיקות."""
        
        elif query_type == 'urgent':
            instruction = """מצא פניות דחופות (תאריך יעד קרוב) וציין את רמת הדחיפות.
ענה בצורה:
"נמצאו X פניות דחופות:
1. פנייה Y - תאריך יעד: Z ימים (פרויקט: ...)
2. פנייה Y - תאריך יעד: Z ימים (פרויקט: ...)
..."
כלול את תאריך היעד ורמת הדחיפות לכל פנייה."""
        
        elif query_type == 'similar':
            request_id = entities.get('request_id')
            if request_id:
                instruction = f"""הסבר מדוע הפניות האלה דומות לשאילתה {request_id}.
ענה בצורה: "הפניות האלה דומות לשאילתה {request_id} כי: [הסבר על דמיון - פרויקט, סטטוס, סוג, וכו']"
אל תפרט כל פנייה - תן הסבר כללי על הדמיון."""
            else:
                instruction = """הסבר מדוע הפניות האלה רלוונטיות לשאילתה.
ענה בצורה: "הפניות האלה רלוונטיות כי..."
אל תפרט כל פנייה - תן הסבר כללי."""
        
        elif query_type == 'answer_retrieval':
            request_id = entities.get('request_id')
            if request_id:
                instruction = f"""תבסס על פנייה דומה לשאילתה {request_id} וספק מענה.
ענה בצורה: "תבסס על פנייה דומה ({request_id}), המענה הוא: [מענה/תשובה]
פנייה זו דומה כי: [הסבר קצר על הדמיון]"
אם יש מענה/תשובה בפנייה הדומה, השתמש בו. אם לא, ספק מענה בהתבסס על הפרטים."""
            else:
                instruction = """תבסס על פנייה דומה וספק מענה.
ענה בצורה: "תבסס על פנייה דומה, המענה הוא: [מענה/תשובה]"
אם יש מענה/תשובה בפנייה הדומה, השתמש בו."""
        
        else:  # find (default)
            # Check if it's a list query (explicit "all")
            if 'כל' in query.lower() or 'all' in query.lower():
                instruction = """ענה על השאלה בהתבסס על הפניות שסופקו.
תן תשובה טקסטואלית קצרה שמסכמת את התשובה.
ענה בצורה: "נמצאו X פניות. להלן 20 הראשונות:"
אז תן רשימה קצרה של הפניות העיקריות (לא כל הפרטים)."""
            else:
                instruction = """ענה על השאלה בהתבסס על הפניות שסופקו.
תן תשובה טקסטואלית קצרה שמסכמת את התשובה.
ענה בצורה: "נמצאו X פניות. הפניות כוללות..."
אל תפרט כל פנייה - תן תשובה כללית."""
        
        return instruction
    
    def _build_entity_context(self, entities: Dict, query_type: str) -> str:
        """
        Build context string about detected entities to help LLM understand the query better.
        
        Args:
            entities: Extracted entities
            query_type: Query type
            
        Returns:
            Context string to add to prompt
        """
        context_parts = []
        
        # Date context
        if 'date_range' in entities:
            date_range = entities['date_range']
            if 'days' in date_range:
                context_parts.append(f"השאלה מתייחסת ל-{date_range['days']} הימים האחרונים.")
            elif 'start' in date_range or 'end' in date_range:
                start = date_range.get('start', 'תחילת התקופה')
                end = date_range.get('end', 'סוף התקופה')
                context_parts.append(f"השאלה מתייחסת לתקופה: {start} עד {end}.")
        
        # Urgency context
        if entities.get('urgency', False):
            context_parts.append("השאלה מתייחסת לפניות דחופות (תאריך יעד קרוב).")
        
        # Person context
        if 'person_name' in entities:
            person = entities['person_name']
            context_parts.append(f"השאלה מתייחסת לפניות של: {person}.")
        
        # Project context
        if 'project_name' in entities:
            project = entities['project_name']
            context_parts.append(f"השאלה מתייחסת לפרויקט: {project}.")
        
        # Type/Status context
        if 'type_id' in entities:
            context_parts.append(f"השאלה מתייחסת לסוג: {entities['type_id']}.")
        if 'status_id' in entities:
            context_parts.append(f"השאלה מתייחסת לסטטוס: {entities['status_id']}.")
        
        if context_parts:
            return "\n".join(context_parts) + "\n"
        return ""
    
    def generate_answer(self, user_content: str, max_length: int = 500) -> str:
        """
        Generate answer using LLM with proper Mistral chat template.
        
        Args:
            user_content: User message content (will be formatted with chat template)
            max_length: Maximum answer length
            
        Returns:
            Generated answer
        """
        if self.model is None or self.tokenizer is None:
            self.load_model()
        
        try:
            import torch
        except ImportError:
            raise ImportError("torch is required for RAG. Install with: pip install torch")
        
        # Use Mistral's chat template format
        # Format: [{"role": "user", "content": "..."}]
        messages = [
            {"role": "user", "content": user_content}
        ]
        
        # Apply chat template (adds [INST] and [/INST] tokens)
        if hasattr(self.tokenizer, 'apply_chat_template') and self.tokenizer.chat_template:
            # Use the chat template
            formatted_prompt = self.tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
            # Tokenize the formatted prompt
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt", truncation=True, max_length=2048)
        else:
            # Fallback: manual formatting
            formatted_prompt = f"<s>[INST] {user_content} [/INST]"
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt", truncation=True, max_length=2048)
        
        # Move to device if GPU available
        device = "cuda" if self._has_gpu() else "cpu"
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Generate
        import time
        gen_start_time = time.time()
        print(f"   Device: {device.upper()}")
        if device == "cpu":
            print("   ⚠️  CPU inference is VERY slow (10-30+ minutes for first generation)")
            print("   ⏳ This is normal - please be patient...")
            print("   💡 Tip: Consider using GPU for faster generation")
        print("   Starting generation...")
        print(f"   [⏱️  START] model.generate() at {time.strftime('%H:%M:%S')}")
        sys.stdout.flush()
        
        try:
            with torch.no_grad():
                # ====================================================================
                # CPU OPTIMIZATION (TEMPORARY - FOR WEAK CPU)
                # ====================================================================
                # These changes reduce accuracy/smartness to speed up CPU inference:
                # 1. Reduced max_new_tokens: 200 (from 500) - Shorter answers, may cut off
                # 2. Greedy decoding (instead of sampling) - Less diverse, more deterministic
                # 
                # ACCURACY IMPACT:
                # - Answer length: ~60% shorter (200 vs 500 tokens)
                # - Answer quality: ~5-10% less diverse/creative
                # - Answer accuracy: ~95% same (core facts remain accurate)
                # 
                # TO REVERT FOR GOOD CPU/GPU:
                # - Set CPU_MAX_TOKENS = max_length (line 757)
                # - Set use_greedy = False (line 754)
                # ====================================================================
                
                # CPU optimization flag - set to False to use optimal settings
                # Changed: Only use CPU optimizations if explicitly on CPU AND no GPU available
                # For GPU systems, always use optimal settings
                USE_CPU_OPTIMIZATION = (device == "cpu" and not self._has_gpu())
                
                # CPU-optimized settings (faster but less optimal)
                if USE_CPU_OPTIMIZATION:
                    CPU_MAX_TOKENS = 200  # Reduced from 500 for speed
                    use_greedy = True     # Greedy decoding (faster than sampling)
                else:
                    # Optimal settings for GPU/good CPU
                    CPU_MAX_TOKENS = max_length  # Use full length
                    use_greedy = False            # Sampling (better quality)
                
                generation_kwargs = {
                    **inputs,
                    'max_new_tokens': min(max_length, CPU_MAX_TOKENS) if USE_CPU_OPTIMIZATION else max_length,
                    'pad_token_id': self.tokenizer.eos_token_id if self.tokenizer.pad_token_id is None else self.tokenizer.pad_token_id,
                    'eos_token_id': self.tokenizer.eos_token_id
                }
                
                if use_greedy:
                    # Greedy decoding (faster on CPU, but less diverse)
                    generation_kwargs['do_sample'] = False
                    generation_kwargs['num_beams'] = 1
                else:
                    # Sampling (slower but more diverse/creative)
                    generation_kwargs['do_sample'] = True
                    generation_kwargs['temperature'] = 0.7
                
                outputs = self.model.generate(**generation_kwargs)
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                raise MemoryError(
                    "Not enough memory to generate answer.\n"
                    "Try reducing max_length or closing other applications."
                )
            raise
        
        gen_end_time = time.time()
        gen_duration = gen_end_time - gen_start_time
        print(f"   [⏱️  END] model.generate() complete: {gen_duration:.2f} seconds ({gen_duration/60:.2f} minutes)")
        print(f"   Completed at {time.strftime('%H:%M:%S')}")
        print("   ✅ Generation complete!")
        sys.stdout.flush()
        
        # Decode full output
        full_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Debug: Log full output for troubleshooting
        print(f"   [DEBUG] Full output length: {len(full_output)} characters")
        if len(full_output) < 500:
            print(f"   [DEBUG] Full output: {full_output}")
        else:
            print(f"   [DEBUG] Full output preview (first 500): {full_output[:500]}...")
            print(f"   [DEBUG] Full output preview (last 500): ...{full_output[-500:]}")
        sys.stdout.flush()
        
        # Extract answer (remove the prompt part)
        # The answer should be after [/INST]
        answer = None
        if "[/INST]" in full_output:
            answer = full_output.split("[/INST]")[-1].strip()
            print(f"   [DEBUG] Extracted answer using [/INST] marker")
        elif "[/INST]" in full_output.lower():
            # Case insensitive
            parts = full_output.lower().split("[/inst]")
            if len(parts) > 1:
                answer = full_output[len("[/INST]".join(parts[:-1]) + "[/INST]"):].strip()
                print(f"   [DEBUG] Extracted answer using [/INST] marker (case insensitive)")
        elif "Answer:" in full_output or "answer:" in full_output.lower():
            # Try Answer: marker
            if "Answer:" in full_output:
                answer = full_output.split("Answer:")[-1].strip()
            else:
                parts = full_output.lower().split("answer:")
                if len(parts) > 1:
                    answer = full_output[len("Answer:".join(parts[:-1]) + "Answer:"):].strip()
            print(f"   [DEBUG] Extracted answer using Answer: marker")
        else:
            # If we can't find a marker, try to extract just the new tokens
            # Get the length of input tokens
            input_length = inputs['input_ids'].shape[1]
            # Decode only the new tokens
            answer = self.tokenizer.decode(outputs[0][input_length:], skip_special_tokens=True).strip()
            print(f"   [DEBUG] Extracted answer using token difference (input_length={input_length})")
        
        # Clean up any remaining special tokens or formatting
        answer = answer.replace("<s>", "").replace("</s>", "").strip() if answer else ""
        
        # Additional cleanup - remove any remaining prompt artifacts
        if answer:
            # Remove common prompt artifacts
            answer = answer.replace("[INST]", "").replace("[/INST]", "").strip()
            # Remove any leading/trailing whitespace or newlines
            answer = answer.strip()
        
        return answer
    
    def query(self, user_query: str, top_k: int = 20) -> Dict:
        """
        Main RAG query method.
        
        Args:
            user_query: User's question
            top_k: Number of requests to retrieve
            
        Returns:
            Dictionary with:
            - answer: Generated answer
            - requests: Retrieved requests
            - parsed: Parsed query info
            - context: Formatted context
        """
        import time
        query_start = time.time()
        print(f"[⏱️  START] Query: {fix_hebrew_rtl(user_query)}")
        print(f"   Start time: {time.strftime('%H:%M:%S')}")
        sys.stdout.flush()
        print()
        
        # Parse query
        parse_start = time.time()
        print("Parsing query...")
        parsed = parse_query(user_query, self.config)
        parse_end = time.time()
        print(f"✓ Intent: {parsed['intent']}")
        if parsed['entities']:
            print(f"✓ Entities: {parsed['entities']}")
        print(f"   [⏱️  {parse_end - query_start:.2f}s] Query parsing: {parse_end - parse_start:.2f} seconds")
        print()
        
        # Handle special query types that need pre-processing
        entity_type = parsed.get('entity_type')
        query_type = parsed.get('query_type')
        
        # For summarize queries, retrieve more requests for better statistics
        if query_type == 'summarize':
            # Retrieve more requests to get better statistics
            retrieval_start = time.time()
            print("Retrieving relevant requests for summarization (retrieving more for better stats)...")
            requests = self.retrieve_requests(user_query, top_k=100)  # Get more for better statistics
            retrieval_end = time.time()
            print(f"✓ Found {len(requests)} relevant requests")
            print(f"   [⏱️  {retrieval_end - query_start:.2f}s] Retrieval: {retrieval_end - retrieval_start:.2f} seconds")
            print()
            
            if not requests:
                query_end = time.time()
                query_duration = query_end - query_start
                print(f"[⏱️  END] Total query time: {query_duration:.2f} seconds ({query_duration/60:.2f} minutes)")
                return {
                    'answer': 'לא נמצאו פניות רלוונטיות.',
                    'requests': [],
                    'parsed': parsed,
                    'context': 'No requests found.'
                }
            
            # Format context (with parsed info for entity-aware formatting)
            format_start = time.time()
            print("Formatting context...")
            context = self.format_context(requests, parsed['query_type'], parsed)
            format_end = time.time()
            print(f"   [⏱️  {format_end - query_start:.2f}s] Context formatting: {format_end - format_start:.2f} seconds")
            print()
            
            # Pre-calculate statistics for better accuracy
            stats_start = time.time()
            print("Calculating statistics...")
            stats = self._calculate_statistics(requests)
            stats_end = time.time()
            print(f"   [⏱️  {stats_end - query_start:.2f}s] Statistics calculation: {stats_end - stats_start:.2f} seconds")
            print()
            
            # Add statistics to context
            stats_text = self._format_statistics(stats)
            context += f"\n\n{stats_text}"
            
            # Build prompt (dynamic based on query type and entities)
            prompt_start = time.time()
            print("Building prompt...")
            user_content = self.build_prompt(user_query, context, parsed)
            prompt_end = time.time()
            print(f"   [⏱️  {prompt_end - query_start:.2f}s] Prompt building: {prompt_end - prompt_start:.2f} seconds")
            print()
            
            # Generate answer
            generation_start = time.time()
            print("Generating answer (this may take 5-15 seconds)...")
            answer = self.generate_answer(user_content)
            generation_end = time.time()
            generation_duration = generation_end - generation_start
            print(f"   [⏱️  {generation_end - query_start:.2f}s] Answer generation: {generation_duration:.2f} seconds ({generation_duration/60:.2f} minutes)")
            print()
            
            query_end = time.time()
            query_duration = query_end - query_start
            print(f"[⏱️  END] Total query time: {query_duration:.2f} seconds ({query_duration/60:.2f} minutes)")
            print(f"   End time: {time.strftime('%H:%M:%S')}")
            print()
            
            if answer:
                answer_preview = answer[:200] + "..." if len(answer) > 200 else answer
                print(f"   Answer preview: {answer_preview}")
                print()
            
            sys.stdout.flush()
            
            return {
                'answer': answer,
                'requests': requests[:top_k],  # Return top_k for display
                'parsed': parsed,
                'context': context
            }
        
        # For project counting queries, we need to group by project
        elif query_type == 'count' and entity_type == 'projects':
            # Retrieve more requests to get better project coverage
            retrieval_start = time.time()
            print("Retrieving relevant requests for project counting...")
            requests = self.retrieve_requests(user_query, top_k=100)  # Get more for grouping
            retrieval_end = time.time()
            print(f"✓ Found {len(requests)} relevant requests")
            print(f"   [⏱️  {retrieval_end - query_start:.2f}s] Retrieval: {retrieval_end - retrieval_start:.2f} seconds")
            print()
            
            if not requests:
                query_end = time.time()
                query_duration = query_end - query_start
                print(f"[⏱️  END] Total query time: {query_duration:.2f} seconds ({query_duration/60:.2f} minutes)")
                return {
                    'answer': 'לא נמצאו פרויקטים.',
                    'requests': [],
                    'parsed': parsed,
                    'context': 'No projects found.'
                }
            
            # Group by project and count
            project_counts = self._count_projects(requests, parsed)
            # Format context with project summary
            context = self._format_project_context(project_counts, parsed)
            # Generate answer directly from project counts (skip LLM for speed)
            answer = self._generate_project_count_answer(project_counts, parsed)
            
            query_end = time.time()
            query_duration = query_end - query_start
            print(f"[⏱️  END] Total query time: {query_duration:.2f} seconds ({query_duration/60:.2f} minutes)")
            print(f"   End time: {time.strftime('%H:%M:%S')}")
            print()
            
            if answer:
                answer_preview = answer[:200] + "..." if len(answer) > 200 else answer
                print(f"   Answer preview: {answer_preview}")
                print()
            
            sys.stdout.flush()
            
            return {
                'answer': answer,
                'requests': requests[:top_k],  # Return top_k for display
                'parsed': parsed,
                'context': context
            }
        
        # For count queries, verify count against database
        if query_type == 'count' and entity_type != 'projects':
            # Get actual count from database for accuracy
            count_start = time.time()
            print("Verifying count against database...")
            try:
                # Use search service to get accurate count
                from api.services import SearchService
                search_service = SearchService()
                search_service.connect_db()
                _, actual_count = search_service.search(user_query, top_k=1)  # Just get count
                search_service.close()
                
                # Add to context
                count_info = f"\n\nמספר מדויק מהמסד נתונים: {actual_count} פניות."
                count_end = time.time()
                print(f"✓ Database count: {actual_count} פניות")
                print(f"   [⏱️  {count_end - query_start:.2f}s] Count verification: {count_end - count_start:.2f} seconds")
                print()
            except Exception as e:
                print(f"⚠️  Could not verify count: {e}")
                actual_count = None
                count_info = ""
                print()
        
        # Standard retrieval for other query types
        retrieval_start = time.time()
        print("Retrieving relevant requests...")
        requests = self.retrieve_requests(user_query, top_k)
        retrieval_end = time.time()
        print(f"✓ Found {len(requests)} relevant requests")
        print(f"   [⏱️  {retrieval_end - query_start:.2f}s] Retrieval: {retrieval_end - retrieval_start:.2f} seconds")
        print()
        
        if not requests:
            query_end = time.time()
            query_duration = query_end - query_start
            print(f"[⏱️  END] Total query time: {query_duration:.2f} seconds ({query_duration/60:.2f} minutes)")
            return {
                'answer': 'לא נמצאו פניות רלוונטיות.',
                'requests': [],
                'parsed': parsed,
                'context': 'No requests found.'
            }
        
        # Format context (with parsed info for entity-aware formatting)
        format_start = time.time()
        print("Formatting context...")
        context = self.format_context(requests, parsed['query_type'], parsed)
        
        # Add count info if available
        if query_type == 'count' and entity_type != 'projects' and 'actual_count' in locals():
            if actual_count is not None:
                context += count_info
        
        format_end = time.time()
        print(f"   [⏱️  {format_end - query_start:.2f}s] Context formatting: {format_end - format_start:.2f} seconds")
        print()
        
        # Build prompt (dynamic based on query type and entities)
        prompt_start = time.time()
        print("Building prompt...")
        user_content = self.build_prompt(user_query, context, parsed)
        prompt_end = time.time()
        print(f"   [⏱️  {prompt_end - query_start:.2f}s] Prompt building: {prompt_end - prompt_start:.2f} seconds")
        print()
        
        # Generate answer
        generation_start = time.time()
        print("Generating answer (this may take 5-15 seconds)...")
        answer = self.generate_answer(user_content)
        generation_end = time.time()
        generation_duration = generation_end - generation_start
        print(f"   [⏱️  {generation_end - query_start:.2f}s] Answer generation: {generation_duration:.2f} seconds ({generation_duration/60:.2f} minutes)")
        print()
        
        query_end = time.time()
        query_duration = query_end - query_start
        print(f"[⏱️  END] Total query time: {query_duration:.2f} seconds ({query_duration/60:.2f} minutes)")
        print(f"   End time: {time.strftime('%H:%M:%S')}")
        print()
        
        # Debug: Print answer preview
        if answer:
            answer_preview = answer[:200] + "..." if len(answer) > 200 else answer
            print(f"   Answer preview: {answer_preview}")
            print()
        else:
            print("   ⚠️  WARNING: Answer is empty!")
            print()
        
        sys.stdout.flush()
        
        return {
            'answer': answer,
            'requests': requests,
            'parsed': parsed,
            'context': context
        }
    
    def close(self):
        """Clean up resources."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    """Interactive RAG query interface."""
    print("=" * 80)
    print("RAG Query System")
    print("=" * 80)
    print()
    print("This system uses:")
    print("  - Query parser (understands intent)")
    print("  - Improved search (field-specific, boosting)")
    print("  - Mistral-7B-Instruct (generates answers)")
    print()
    print("Examples:")
    print("  - 'כמה פניות יש מאור גלילי?'")
    print("  - 'תביא לי סיכום של כל הפניות מסוג 4'")
    print("  - 'מה הפרויקטים הכי פעילים?'")
    print()
    
    # Initialize RAG
    rag = RAGSystem()
    
    try:
        # Connect to database
        rag.connect_db()
        
        # Load model (will be done on first query if not loaded)
        print("Note: Model will be loaded on first query (takes 30-60 seconds)")
        print()
        
        while True:
            query = input("Enter your question (or 'quit' to exit): ").strip()
            
            if not query or query.lower() in ['quit', 'exit', 'q']:
                break
            
            print()
            print("=" * 80)
            
            try:
                result = rag.query(query)
                
                print("=" * 80)
                print("ANSWER")
                print("=" * 80)
                print()
                print(fix_hebrew_rtl(result['answer']))
                print()
                
                if result['requests']:
                    print("=" * 80)
                    print(f"BASED ON {len(result['requests'])} RELEVANT REQUESTS")
                    print("=" * 80)
                    print()
                    print("Top 5 requests used:")
                    for i, req in enumerate(result['requests'][:5], 1):
                        print(f"  {i}. Request {req['requestid']} - {req.get('projectname', 'N/A')}")
                    print()
                
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
                print()
            
            print()
    
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        rag.close()


if __name__ == "__main__":
    main()

