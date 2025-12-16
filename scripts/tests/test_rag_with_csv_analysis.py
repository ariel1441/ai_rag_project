"""
RAG Testing with CSV Analysis
Shows expected results from CSV and prepares for RAG testing
"""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def analyze_csv_for_tests():
    """Analyze CSV to show what we expect from RAG."""
    csv_path = Path(__file__).parent.parent.parent / "data" / "raw" / "request.csv"
    
    if not csv_path.exists():
        print("❌ CSV file not found")
        return
    
    print("="*80)
    print("CSV DATA ANALYSIS - Expected Results for RAG Tests")
    print("="*80)
    print()
    
    df = pd.read_csv(csv_path, encoding='utf-8-sig', low_memory=False)
    print(f"✓ Loaded {len(df)} requests from CSV")
    print()
    
    # Test 1: Count requests from יניב ליבוביץ
    print("="*80)
    print("TEST 1: Count requests from יניב ליבוביץ")
    print("="*80)
    mask = df['UpdatedBy'].astype(str).str.contains('יניב ליבוביץ', na=False, case=False, regex=False)
    count = mask.sum()
    print(f"Expected count: {count}")
    print(f"\nSample requests (first 5):")
    sample = df[mask].head(5)
    for idx, row in sample.iterrows():
        print(f"  Request {row['RequestId']}: {row.get('ProjectName', 'N/A')}")
        print(f"    Updated By: {row.get('UpdatedBy', 'N/A')}")
        print(f"    Type: {row.get('RequestTypeId', 'N/A')}")
    print()
    
    # Test 2: Count requests from אוקסנה כלפון
    print("="*80)
    print("TEST 2: Count requests from אוקסנה כלפון")
    print("="*80)
    mask = df['UpdatedBy'].astype(str).str.contains('אוקסנה כלפון', na=False, case=False, regex=False)
    count = mask.sum()
    print(f"Expected count: {count}")
    print(f"\nSample requests (first 5):")
    sample = df[mask].head(5)
    for idx, row in sample.iterrows():
        print(f"  Request {row['RequestId']}: {row.get('ProjectName', 'N/A')}")
        print(f"    Updated By: {row.get('UpdatedBy', 'N/A')}")
    print()
    
    # Test 3: Count requests of type 1
    print("="*80)
    print("TEST 3: Count requests of type 1")
    print("="*80)
    mask = df['RequestTypeId'] == 1
    count = mask.sum()
    print(f"Expected count: {count}")
    print(f"\nSample requests (first 5):")
    sample = df[mask].head(5)
    for idx, row in sample.iterrows():
        print(f"  Request {row['RequestId']}: {row.get('ProjectName', 'N/A')}")
        print(f"    Type: {row.get('RequestTypeId', 'N/A')}")
        print(f"    Updated By: {row.get('UpdatedBy', 'N/A')}")
    print()
    
    # Test 4: Count requests of type 2
    print("="*80)
    print("TEST 4: Count requests of type 2")
    print("="*80)
    mask = df['RequestTypeId'] == 2
    count = mask.sum()
    print(f"Expected count: {count}")
    print()
    
    # Test 5: Find requests from יניב ליבוביץ (sample)
    print("="*80)
    print("TEST 5: Find requests from יניב ליבוביץ (sample)")
    print("="*80)
    mask = df['UpdatedBy'].astype(str).str.contains('יניב ליבוביץ', na=False, case=False, regex=False)
    sample = df[mask].head(10)
    print(f"Expected to find: {len(sample)} requests (showing first 10)")
    for idx, row in sample.iterrows():
        print(f"  Request {row['RequestId']}:")
        print(f"    Project: {row.get('ProjectName', 'N/A')}")
        print(f"    Updated By: {row.get('UpdatedBy', 'N/A')}")
        print(f"    Created By: {row.get('CreatedBy', 'N/A')}")
        print(f"    Type: {row.get('RequestTypeId', 'N/A')}")
        print(f"    Status: {row.get('RequestStatusId', 'N/A')}")
    print()
    
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total requests in CSV: {len(df)}")
    print(f"Unique UpdatedBy values: {df['UpdatedBy'].nunique()}")
    print(f"Unique RequestTypeId values: {sorted(df['RequestTypeId'].dropna().unique())}")
    print()
    print("Top 10 UpdatedBy values:")
    print(df['UpdatedBy'].value_counts().head(10))

if __name__ == "__main__":
    analyze_csv_for_tests()

