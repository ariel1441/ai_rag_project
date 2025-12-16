"""
Test Model Loading with Better Error Handling
This will show exactly what error occurs if loading fails.
"""
import sys
import traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.core.rag_query import RAGSystem

def main():
    print("="*80)
    print("MODEL LOADING TEST - WITH ERROR HANDLING")
    print("="*80)
    print()
    
    try:
        print("Step 1: Initializing RAG system...")
        rag = RAGSystem()
        print("✅ RAG system initialized")
        print()
        
        print("Step 2: Loading model...")
        print("="*80)
        print("This will attempt to load with float16...")
        print("If it fails, you'll see the exact error below.")
        print("="*80)
        print()
        
        rag.load_model()
        
        print()
        print("="*80)
        print("✅ MODEL LOADED SUCCESSFULLY!")
        print("="*80)
        print()
        print("Model is ready to use.")
        print("You can now run queries.")
        
    except KeyboardInterrupt:
        print()
        print("="*80)
        print("⚠️  Process interrupted by user (Ctrl+C)")
        print("="*80)
    except Exception as e:
        print()
        print("="*80)
        print("❌ ERROR OCCURRED")
        print("="*80)
        print()
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print()
        print("Full traceback:")
        print("-" * 80)
        traceback.print_exc()
        print("-" * 80)
        print()
        print("Possible causes:")
        print("  1. Out of memory - close other applications")
        print("  2. Model files missing - check model path")
        print("  3. Corrupted model files - re-download model")
        print("  4. Library version mismatch - update packages")

if __name__ == '__main__':
    main()

