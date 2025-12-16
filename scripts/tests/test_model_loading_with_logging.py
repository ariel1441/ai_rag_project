"""
Test model loading with enhanced logging to diagnose stuck issues.
"""
import sys
import time
import logging
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('model_loading_test.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

print("="*80)
print("MODEL LOADING TEST - WITH ENHANCED LOGGING")
print("="*80)
print()
print("This test loads the model with detailed logging to diagnose issues.")
print("All output will be saved to: model_loading_test.log")
print()

try:
    from scripts.core.rag_query import RAGSystem
    import psutil
    import os
    
    # Check initial state
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / (1024**3)  # GB
    cpu_before = process.cpu_percent(interval=1)
    
    print(f"Initial state:")
    print(f"  Memory: {mem_before:.2f} GB")
    print(f"  CPU: {cpu_before:.1f}%")
    print()
    
    logger.info("Initializing RAG system...")
    print("Step 1: Initializing RAG system...")
    rag = RAGSystem()
    print("✅ RAG system initialized")
    logger.info("RAG system initialized")
    print()
    
    print("Step 2: Loading model...")
    print("⚠️  This will take 2-5 minutes on CPU.")
    print("    Progress will be logged every 10 seconds.")
    print()
    
    start_time = time.time()
    last_log_time = start_time
    
    def check_progress():
        """Check and log progress periodically."""
        global last_log_time
        current_time = time.time()
        elapsed = current_time - start_time
        
        # Log every 10 seconds
        if current_time - last_log_time >= 10:
            process = psutil.Process(os.getpid())
            mem_current = process.memory_info().rss / (1024**3)  # GB
            cpu_current = process.cpu_percent(interval=0.1)
            mem_delta = mem_current - mem_before
            
            logger.info(f"[{elapsed:.0f}s] Memory: {mem_current:.2f} GB (+{mem_delta:.2f} GB), CPU: {cpu_current:.1f}%")
            print(f"   [{elapsed:.0f}s] Memory: {mem_current:.2f} GB (+{mem_delta:.2f} GB), CPU: {cpu_current:.1f}%")
            sys.stdout.flush()
            
            last_log_time = current_time
    
    # Start a simple monitoring thread (or just check before/after)
    print("Starting model load...")
    logger.info("Starting model load...")
    sys.stdout.flush()
    
    try:
        # Load model (this will take time)
        # We can't easily interrupt it, but we can log before/after
        rag.load_model()
        
        load_time = time.time() - start_time
        
        # Check final state
        process = psutil.Process(os.getpid())
        mem_after = process.memory_info().rss / (1024**3)  # GB
        cpu_after = process.cpu_percent(interval=1)
        mem_used = mem_after - mem_before
        
        print()
        print("="*80)
        print("✅ MODEL LOADED SUCCESSFULLY")
        print("="*80)
        print(f"Total time: {load_time:.1f} seconds ({load_time/60:.1f} minutes)")
        print(f"Memory used: {mem_used:.2f} GB")
        print(f"Final memory: {mem_after:.2f} GB")
        print(f"Final CPU: {cpu_after:.1f}%")
        print()
        
        logger.info(f"Model loaded successfully in {load_time:.1f} seconds")
        logger.info(f"Memory used: {mem_used:.2f} GB")
        
        # Test a simple query
        print("Step 3: Testing model with a simple query...")
        logger.info("Testing model with simple query...")
        
        test_query = "כמה פניות יש?"
        print(f"Query: {test_query}")
        
        query_start = time.time()
        result = rag.query(test_query, top_k=5)
        query_time = time.time() - query_start
        
        print(f"✅ Query completed in {query_time:.1f} seconds")
        print(f"Answer: {result.get('answer', 'No answer')[:100]}...")
        print()
        
        logger.info(f"Query completed in {query_time:.1f} seconds")
        
        print("="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print()
        print("Model is working correctly!")
        print("Check model_loading_test.log for detailed logs.")
        
    except Exception as e:
        load_time = time.time() - start_time
        error_type = type(e).__name__
        error_msg = str(e)
        
        print()
        print("="*80)
        print("❌ MODEL LOADING FAILED")
        print("="*80)
        print(f"Time before failure: {load_time:.1f} seconds ({load_time/60:.1f} minutes)")
        print(f"Error Type: {error_type}")
        print(f"Error Message: {error_msg}")
        print()
        
        logger.error(f"Model loading failed after {load_time:.1f} seconds")
        logger.error(f"Error: {error_type}: {error_msg}", exc_info=True)
        
        import traceback
        traceback.print_exc()
        
        print("="*80)
        print()
        print("Check model_loading_test.log for full error details.")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Failed to import or initialize: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


