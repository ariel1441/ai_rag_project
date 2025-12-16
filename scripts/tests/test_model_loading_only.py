"""
Test ONLY model loading - to see if it works without crashing.
This is a minimal test to isolate the loading issue.
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

print("="*80)
print("MODEL LOADING TEST - ISOLATED")
print("="*80)
print()
print("This test ONLY loads the model (no queries, no database).")
print("Purpose: See if model loading works without crashing.")
print()

try:
    from scripts.core.rag_query import RAGSystem
    
    print("Step 1: Initializing RAG system...")
    rag = RAGSystem()
    print("✅ RAG system initialized")
    print()
    
    print("Step 2: Loading model...")
    print("⚠️  This will take 1-2 minutes.")
    print("    You'll see: Loading checkpoint shards: 33% → 66% → 100%")
    print("    If it crashes, we'll see the error.")
    print()
    
    start_time = time.time()
    
    try:
        rag.load_model()
        load_time = time.time() - start_time
        
        print()
        print("="*80)
        print("✅ SUCCESS! Model loaded successfully!")
        print("="*80)
        print(f"Loading time: {load_time:.2f} seconds ({load_time/60:.1f} minutes)")
        print()
        print("The model is now in memory and ready to use.")
        print("You can now run queries (they'll be fast - 5-15 seconds).")
        print()
        
        # Cleanup
        rag.close()
        
    except MemoryError as e:
        print()
        print("="*80)
        print("❌ MEMORY ERROR")
        print("="*80)
        print(str(e))
        print()
        print("Solutions:")
        print("  1. Close other applications to free RAM")
        print("  2. Restart computer to free cached RAM")
        print("  3. Need at least 8GB free RAM for float16 model")
        print()
        
    except Exception as e:
        print()
        print("="*80)
        print("❌ ERROR LOADING MODEL")
        print("="*80)
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print()
        print("Full error details:")
        import traceback
        traceback.print_exc()
        print()
        print("This error needs to be fixed before RAG can work.")
        print()

except KeyboardInterrupt:
    print("\n\nTest interrupted by user")
except Exception as e:
    print(f"\n\n❌ Fatal error: {e}")
    import traceback
    traceback.print_exc()

