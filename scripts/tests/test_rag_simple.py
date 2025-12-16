"""
Simple RAG Test - Test one query at a time
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.core.rag_query import RAGSystem
from scripts.utils.hebrew import fix_hebrew_rtl

def test_single_query(query: str):
    """Test RAG with a single query."""
    print("="*80)
    print("RAG SYSTEM TEST")
    print("="*80)
    print()
    
    rag = RAGSystem()
    
    try:
        # Connect to database
        print("Connecting to database...")
        rag.connect_db()
        print("✓ Database connected")
        print()
        
        # Run query
        print(f"Query: {fix_hebrew_rtl(query)}")
        print()
        
        result = rag.query(query, top_k=20)
        
        print("\n" + "="*80)
        print("ANSWER")
        print("="*80)
        print(fix_hebrew_rtl(result['answer']))
        print()
        
        print("="*80)
        print(f"RETRIEVED {len(result['requests'])} REQUESTS")
        print("="*80)
        for i, req in enumerate(result['requests'][:10], 1):
            print(f"{i}. Request {req['requestid']}")
            if req.get('projectname'):
                print(f"   Project: {fix_hebrew_rtl(str(req['projectname']))}")
            if req.get('updatedby'):
                print(f"   Updated By: {fix_hebrew_rtl(str(req['updatedby']))}")
            if req.get('createdby'):
                print(f"   Created By: {fix_hebrew_rtl(str(req['createdby']))}")
            print(f"   Similarity: {req.get('similarity', 0):.4f}")
            print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        rag.close()

if __name__ == "__main__":
    # Test with a simple query
    query = "כמה פניות יש מיניב ליבוביץ?"
    test_single_query(query)

