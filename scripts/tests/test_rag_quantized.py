"""
Test RAG system with quantized model.
Verifies that model loads correctly with 4-bit quantization.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.core.rag_query import RAGSystem

def test_rag_loading():
    """Test that RAG system loads model correctly."""
    print("=" * 80)
    print("Testing RAG System with Quantized Model")
    print("=" * 80)
    print()
    
    try:
        # Initialize RAG system
        print("1. Initializing RAG system...")
        rag = RAGSystem()
        print("   ✅ RAG system initialized")
        print()
        
        # Connect to database
        print("2. Connecting to database...")
        rag.connect_db()
        print("   ✅ Database connected")
        print()
        
        # Load model (this is the critical test)
        print("3. Loading model with 4-bit quantization...")
        print("   (This should use ~4GB RAM instead of 15GB)")
        print()
        rag.load_model()
        print()
        print("   ✅ Model loaded successfully!")
        print()
        
        # Test a simple query
        print("4. Testing a simple query...")
        test_query = "כמה פניות יש?"
        print(f"   Query: {test_query}")
        print()
        
        result = rag.query(test_query, top_k=5)
        
        print("   ✅ Query executed successfully!")
        print()
        print("   Answer:")
        print(f"   {result['answer']}")
        print()
        
        # Cleanup
        print("5. Cleaning up...")
        rag.close()
        print("   ✅ Cleanup complete")
        print()
        
        print("=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print()
        print("The quantized model is working correctly!")
        print("You can now use: python scripts/core/rag_query.py")
        print()
        
        return True
        
    except MemoryError as e:
        print()
        print("=" * 80)
        print("❌ MEMORY ERROR")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        print()
        print("This means there's still not enough free RAM.")
        print("Solutions:")
        print("  1. Close other applications")
        print("  2. Restart computer (frees cached RAM)")
        print("  3. Check for stuck Python processes")
        print()
        return False
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR")
        print("=" * 80)
        print()
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        print()
        return False

if __name__ == "__main__":
    success = test_rag_loading()
    sys.exit(0 if success else 1)

