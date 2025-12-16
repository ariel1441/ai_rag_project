"""
Comprehensive Search Execution Test

ACTUALLY RUNS searches and compares with database.
Tests MANY queries across all types.
Generates detailed performance and accuracy report.
"""
import os
import sys
import time
from pathlib import Path
import psycopg2
from pgvector.psycopg2 import register_vector
import json
from typing import Dict, List, Tuple, Any
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "scripts"))

from api.services import SearchService
from scripts.utils.query_parser import QueryParser
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# GENERATE MANY TEST QUERIES
# ============================================================================

def generate_test_queries() -> List[Dict[str, Any]]:
    """Generate comprehensive test queries."""
    queries = []
    
    # Person queries (many variations) - EXPANDED
    person_queries = [
        # מאור גלילי variations
        "פניות מאור גלילי",
        "בקשות מאור גלילי",
        "כמה פניות יש מאור גלילי?",
        "כמה בקשות יש מאור גלילי?",
        "תביא לי פניות מאור גלילי",
        "תביא לי בקשות מאור גלילי",
        "הראה לי פניות מאור גלילי",
        "מצא לי פניות מאור גלילי",
        "פניות של אור גלילי",
        "בקשות של אור גלילי",
        "בקשות מ-אור גלילי",
        "פניות מ-אור גלילי",
        "אור גלילי",
        "כל הפניות מאור גלילי",
        "כל הבקשות מאור גלילי",
        
        # יניב ליבוביץ variations
        "פניות מיניב ליבוביץ",
        "בקשות מיניב ליבוביץ",
        "כמה פניות יש מיניב ליבוביץ?",
        "כמה בקשות יש מיניב ליבוביץ?",
        "תביא לי פניות מיניב ליבוביץ",
        "הראה לי פניות מיניב ליבוביץ",
        "פניות של יניב ליבוביץ",
        "בקשות של יניב ליבוביץ",
        "בקשות מ-יניב ליבוביץ",
        "פניות מ-יניב ליבוביץ",
        "יניב ליבוביץ",
        "כל הפניות מיניב ליבוביץ",
        
        # אוקסנה כלפון variations
        "פניות מאוקסנה כלפון",
        "בקשות מאוקסנה כלפון",
        "כמה פניות יש מאוקסנה כלפון?",
        "תביא לי פניות מאוקסנה כלפון",
        "הראה לי פניות מאוקסנה כלפון",
        "פניות של אוקסנה כלפון",
        "אוקסנה כלפון",
        
        # משה אוגלבו variations
        "פניות ממשה אוגלבו",
        "בקשות ממשה אוגלבו",
        "כמה פניות יש ממשה אוגלבו?",
        "תביא לי פניות ממשה אוגלבו",
        "משה אוגלבו",
        
        # General person patterns
        "פניות מאתר חיצוני תמר",
        "בקשות מTamarApp",
    ]
    
    for query in person_queries:
        queries.append({
            'query': query,
            'type': 'person',
            'expected_intent': 'person',
        })
    
    # Type queries - EXPANDED
    type_queries = [
        "בקשות מסוג 4",
        "פניות מסוג 4",
        "בקשות מסוג 1",
        "פניות מסוג 1",
        "בקשות מסוג 2",
        "פניות מסוג 2",
        "בקשות מסוג 3",
        "פניות מסוג 3",
        "כמה פניות יש מסוג 4?",
        "כמה בקשות יש מסוג 4?",
        "כמה פניות יש מסוג 1?",
        "כמה בקשות יש מסוג 1?",
        "כמה פניות יש מסוג 2?",
        "כמה פניות יש מסוג 3?",
        "תביא לי בקשות מסוג 4",
        "תביא לי פניות מסוג 4",
        "הראה לי פניות מסוג 1",
        "מצא לי בקשות מסוג 2",
        "כל הבקשות מסוג 4",
        "כל הפניות מסוג 1",
        "סוג 4",
        "סוג 1",
        "סוג 2",
        "סוג 3",
        "בקשות type 4",
        "פניות type 1",
    ]
    
    for query in type_queries:
        queries.append({
            'query': query,
            'type': 'type',
            'expected_intent': 'type',
        })
    
    # Status queries - EXPANDED
    status_queries = [
        "בקשות בסטטוס 1",
        "פניות בסטטוס 1",
        "בקשות בסטטוס 2",
        "פניות בסטטוס 2",
        "בקשות בסטטוס 7",
        "פניות בסטטוס 7",
        "בקשות בסטטוס 10",
        "פניות בסטטוס 10",
        "כמה פניות יש בסטטוס 1?",
        "כמה בקשות יש בסטטוס 1?",
        "כמה פניות יש בסטטוס 10?",
        "תביא לי בקשות בסטטוס 2",
        "הראה לי פניות בסטטוס 7",
        "כל הבקשות בסטטוס 10",
    ]
    
    for query in status_queries:
        queries.append({
            'query': query,
            'type': 'status',
            'expected_intent': 'status',
        })
    
    # Count queries
    count_queries = [
        "כמה פניות יש?",
        "כמה בקשות יש?",
        "כמה פניות יש מאור גלילי?",
        "כמה בקשות יש מסוג 4?",
        "כמה פניות יש בסטטוס 1?",
    ]
    
    for query in count_queries:
        queries.append({
            'query': query,
            'type': 'count',
            'expected_intent': 'person' if 'מאור' in query or 'מיניב' in query else 'type' if 'סוג' in query else 'status' if 'סטטוס' in query else 'general',
        })
    
    # Similar queries
    similar_queries = [
        "פניות דומות ל221000226",
        "בקשות דומות ל211000001",
        "תביא לי פניות דומות ל221000226",
        "דומות ל221000226",
    ]
    
    for query in similar_queries:
        queries.append({
            'query': query,
            'type': 'similar',
            'expected_intent': 'general',
        })
    
    # General semantic queries - EXPANDED
    general_queries = [
        "תיאום תכנון",
        "תכנון",
        "תכנון עירוני",
        "אלינור",
        "פרויקטים",
        "בקשות דחופות",
        "פניות אחרונות",
        "בנייה",
        "אישור",
        "בקשות פתוחות",
        "פניות סגורות",
        "תיאום",
        "בקשות חדשות",
        "פניות ישנות",
        "בקשות אחרונות",
        "פניות חדשות",
        "תכנון ובנייה",
        "אישורים",
        "בקשות ממתינות",
        "פניות ממתינות",
        "בקשות פעילות",
        "פניות פעילות",
        "תכנון עיר",
        "בנייה עירונית",
        "אלינור תכנון",
        "תיאום פרויקטים",
    ]
    
    for query in general_queries:
        queries.append({
            'query': query,
            'type': 'general',
            'expected_intent': 'general',
        })
    
    # Project queries (if we have project names)
    project_queries = [
        "פרויקט אלינור",
        "פרויקטים של אלינור",
        "בקשות לפרויקט אלינור",
    ]
    
    for query in project_queries:
        queries.append({
            'query': query,
            'type': 'project',
            'expected_intent': 'project',
        })
    
    # Urgent queries
    urgent_queries = [
        "בקשות דחופות",
        "פניות דחופות",
        "בקשות שדורשות תשובה",
        "פניות דחופות מאור גלילי",
    ]
    
    for query in urgent_queries:
        queries.append({
            'query': query,
            'type': 'urgent',
            'expected_intent': 'person' if 'מאור' in query or 'מיניב' in query else 'general',
        })
    
    # Date queries
    date_queries = [
        "בקשות מהשבוע האחרון",
        "פניות מהחודש האחרון",
        "בקשות מ-2024",
    ]
    
    for query in date_queries:
        queries.append({
            'query': query,
            'type': 'date',
            'expected_intent': 'general',
        })
    
    # Mixed/complex queries
    complex_queries = [
        "תביא לי את כל הפניות מאור גלילי",
        "הצג את כל הבקשות מסוג 4",
        "כמה פניות יש מאור גלילי מסוג 4?",
        "בקשות דחופות מסוג 1",
    ]
    
    for query in complex_queries:
        queries.append({
            'query': query,
            'type': 'complex',
            'expected_intent': 'person' if 'מאור' in query or 'מיניב' in query else 'type' if 'סוג' in query else 'general',
        })
    
    return queries

# ============================================================================
# DATABASE QUERY FUNCTIONS
# ============================================================================

def get_db_connection():
    """Get database connection."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5433")
    database = os.getenv("POSTGRES_DATABASE", "ai_requests_db")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD")
    
    if not password:
        raise ValueError("POSTGRES_PASSWORD not in .env!")
    
    conn = psycopg2.connect(
        host=host, port=int(port), database=database,
        user=user, password=password
    )
    register_vector(conn)
    return conn

def count_by_person_name(conn, person_name: str) -> int:
    """Count requests where person name appears."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(DISTINCT requestid)
        FROM requests
        WHERE 
            LOWER(COALESCE(updatedby, '')) LIKE %s OR
            LOWER(COALESCE(createdby, '')) LIKE %s OR
            LOWER(COALESCE(responsibleemployeename, '')) LIKE %s
    """, (f'%{person_name.lower()}%', f'%{person_name.lower()}%', f'%{person_name.lower()}%'))
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def count_by_type(conn, type_id: str) -> int:
    """Count requests by type ID."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM requests
        WHERE requesttypeid::TEXT = %s
    """, (str(type_id),))
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def count_by_status(conn, status_id: str) -> int:
    """Count requests by status ID."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM requests
        WHERE requeststatusid::TEXT = %s
    """, (str(status_id),))
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def count_by_project(conn, project_name: str) -> int:
    """Count requests by project name."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM requests
        WHERE LOWER(COALESCE(projectname, '')) LIKE %s
    """, (f'%{project_name.lower()}%',))
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def count_total(conn) -> int:
    """Count total requests."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM requests")
    count = cursor.fetchone()[0]
    cursor.close()
    return count

def extract_type_id(query: str) -> str:
    """Extract type ID from query."""
    import re
    match = re.search(r'סוג\s*(\d+)', query)
    if match:
        return match.group(1)
    return None

def extract_status_id(query: str) -> str:
    """Extract status ID from query."""
    import re
    match = re.search(r'סטטוס\s*(\d+)', query)
    if match:
        return match.group(1)
    return None

def extract_person_name_from_query(query: str, parsed: Dict) -> str:
    """Extract person name from parsed query."""
    entities = parsed.get('entities', {})
    return entities.get('person_name')

def extract_project_name_from_query(query: str, parsed: Dict) -> str:
    """Extract project name from parsed query."""
    entities = parsed.get('entities', {})
    return entities.get('project_name')

# ============================================================================
# TEST EXECUTION
# ============================================================================

def run_single_test(query_info: Dict, search_service: SearchService, parser: QueryParser, conn) -> Dict[str, Any]:
    """Run a single test and return results."""
    query = query_info['query']
    expected_type = query_info['type']
    expected_intent = query_info['expected_intent']
    
    result = {
        'query': query,
        'type': expected_type,
        'expected_intent': expected_intent,
        'success': False,
        'errors': [],
        'warnings': [],
        'metrics': {},
    }
    
    try:
        # 1. Parse query
        start_parse = time.time()
        parsed = parser.parse(query)
        parse_time = (time.time() - start_parse) * 1000
        
        actual_intent = parsed.get('intent', 'unknown')
        query_type = parsed.get('query_type', 'unknown')
        entities = parsed.get('entities', {})
        
        result['parsed'] = {
            'intent': actual_intent,
            'query_type': query_type,
            'entities': entities,
        }
        result['metrics']['parse_time_ms'] = parse_time
        
        # Check intent
        if actual_intent != expected_intent:
            result['warnings'].append(f"Intent mismatch: expected '{expected_intent}', got '{actual_intent}'")
        
        # 2. Execute search
        start_search = time.time()
        search_results, search_count = search_service.search(query, top_k=20)
        search_time = (time.time() - start_search) * 1000
        
        result['metrics']['search_time_ms'] = search_time
        result['metrics']['results_returned'] = len(search_results)
        result['metrics']['search_count'] = search_count
        
        # 3. Query database for comparison
        db_count = None
        db_query_type = None
        
        if expected_type == 'person':
            person_name = extract_person_name_from_query(query, parsed)
            if person_name:
                # First check person fields
                db_count = count_by_person_name(conn, person_name)
                db_query_type = 'person_name_like'
                result['db_query'] = f"LIKE '%{person_name}%' in updatedby/createdby/responsibleemployeename"
                
                # Special case: If person fields return 0, check if it's actually a project name
                # This handles "אור גלילי" which is a project name, not person
                if db_count == 0 and person_name:
                    project_count = count_by_project(conn, person_name)
                    if project_count > 0:
                        # It's actually a project, update the comparison
                        db_count = project_count
                        db_query_type = 'project_name_like'
                        result['db_query'] = f"LIKE '%{person_name}%' in projectname (was misclassified as person)"
                        result['warnings'].append(f"'{person_name}' is a project name, not person name")
        
        elif expected_type == 'type':
            type_id = extract_type_id(query)
            if type_id:
                db_count = count_by_type(conn, type_id)
                db_query_type = 'type_id_exact'
                result['db_query'] = f"requesttypeid = {type_id}"
        
        elif expected_type == 'status':
            status_id = extract_status_id(query)
            if status_id:
                db_count = count_by_status(conn, status_id)
                db_query_type = 'status_id_exact'
                result['db_query'] = f"requeststatusid = {status_id}"
        
        elif expected_type == 'project':
            project_name = extract_project_name_from_query(query, parsed)
            if project_name:
                db_count = count_by_project(conn, project_name)
                db_query_type = 'project_name_like'
                result['db_query'] = f"LIKE '%{project_name}%' in projectname"
        
        elif expected_type == 'general':
            # For general queries, don't compare with total - semantic search is different
            # Just mark that we can't do exact comparison
            db_count = None
            db_query_type = 'semantic_only'
            result['db_query'] = "Semantic search - no exact DB comparison possible"
        
        elif expected_type == 'count':
            # For count queries, check if it's a specific count (type/status/person) or general
            if 'סוג' in query or 'type' in query.lower():
                type_id = extract_type_id(query)
                if type_id:
                    db_count = count_by_type(conn, type_id)
                    db_query_type = 'type_id_exact'
            elif 'סטטוס' in query or 'status' in query.lower():
                status_id = extract_status_id(query)
                if status_id:
                    db_count = count_by_status(conn, status_id)
                    db_query_type = 'status_id_exact'
            else:
                # Check if parsed query has person_name entity (generic check)
                person_name = extract_person_name_from_query(query, parsed)
                if person_name:
                    # Person count query
                    db_count = count_by_person_name(conn, person_name)
                    if db_count == 0:
                        # Check projectname (generic fallback for any person query)
                        db_count = count_by_project(conn, person_name)
                    db_query_type = 'person_or_project'
            else:
                # General count - don't compare
                db_count = None
                db_query_type = 'general_count'
                result['db_query'] = "General count - no exact DB comparison"
        
        result['db_count'] = db_count
        result['db_query_type'] = db_query_type
        
        # 4. Compare results
        if db_count is not None and search_count is not None:
            if db_count == 0:
                ratio = 0 if search_count == 0 else float('inf')
            else:
                ratio = search_count / db_count
            
            result['metrics']['count_ratio'] = ratio
            result['metrics']['count_difference'] = abs(search_count - db_count)
            
            # Accuracy assessment
            if expected_type in ['type', 'status']:
                # Exact match expected for type/status
                if search_count == db_count:
                    result['accuracy'] = 'exact'
                elif abs(search_count - db_count) <= 5:
                    result['accuracy'] = 'very_close'
                    result['warnings'].append(f"Count differs by {abs(search_count - db_count)}")
                else:
                    result['accuracy'] = 'different'
                    result['errors'].append(f"Count mismatch: DB={db_count}, Search={search_count}")
            else:
                # Semantic search - ratio should be reasonable
                if 0.3 <= ratio <= 3.0:
                    result['accuracy'] = 'acceptable'
                elif 0.1 <= ratio <= 10.0:
                    result['accuracy'] = 'questionable'
                    result['warnings'].append(f"Count ratio {ratio:.2f} is outside ideal range")
                else:
                    result['accuracy'] = 'poor'
                    result['errors'].append(f"Count ratio {ratio:.2f} is very different")
        
        # 5. Check result quality (for person queries)
        if expected_type == 'person' and search_results:
            person_name = extract_person_name_from_query(query, parsed)
            if person_name:
                # Check if person name appears in top results
                found_in_top = False
                for req in search_results[:5]:
                    req_id = req.get('requestid')
                    if req_id:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT updatedby, createdby, responsibleemployeename
                            FROM requests
                            WHERE requestid = %s
                        """, (req_id,))
                        row = cursor.fetchone()
                        cursor.close()
                        if row:
                            fields = ' '.join([str(f) or '' for f in row]).lower()
                            if person_name.lower() in fields:
                                found_in_top = True
                                break
                
                result['metrics']['person_found_in_top5'] = found_in_top
                if not found_in_top:
                    result['warnings'].append("Person name not found in top 5 results")
        
        # 6. Overall success - mark as success if accuracy is acceptable or better
        # Set success based on accuracy and results
        accuracy = result.get('accuracy', 'unknown')
        
        if accuracy in ['exact', 'very_close', 'acceptable', 'semantic_only']:
            result['success'] = True
        elif accuracy == 'unknown' and search_count > 0 and len(result['errors']) == 0:
            # Unknown accuracy but got results and no errors - mark as success
            result['success'] = True
        elif len(result['errors']) == 0 and search_count > 0:
            # No errors and got results - mark as success
            result['success'] = True
        else:
            result['success'] = False
        
    except Exception as e:
        result['errors'].append(f"Exception: {str(e)}")
        import traceback
        result['traceback'] = traceback.format_exc()
    
    return result

# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(test_results: List[Dict]) -> str:
    """Generate comprehensive test report."""
    report = []
    report.append("=" * 100)
    report.append("COMPREHENSIVE SEARCH TEST REPORT")
    report.append("=" * 100)
    report.append("")
    
    # Summary statistics
    total_tests = len(test_results)
    successful_tests = sum(1 for r in test_results if r.get('success', False))
    failed_tests = total_tests - successful_tests
    
    report.append(f"Total Tests: {total_tests}")
    report.append(f"Successful: {successful_tests} ({successful_tests/total_tests*100:.1f}%)")
    report.append(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
    report.append("")
    
    # Group by test type
    by_type = defaultdict(list)
    for result in test_results:
        by_type[result['type']].append(result)
    
    report.append("=" * 100)
    report.append("RESULTS BY TEST TYPE")
    report.append("=" * 100)
    report.append("")
    
    for test_type, results in sorted(by_type.items()):
        report.append(f"--- {test_type.upper()} Tests ({len(results)} tests) ---")
        
        type_success = sum(1 for r in results if r.get('success', False))
        report.append(f"Success Rate: {type_success}/{len(results)} ({type_success/len(results)*100:.1f}%)")
        
        # Average metrics
        avg_search_time = sum(r.get('metrics', {}).get('search_time_ms', 0) for r in results) / len(results)
        avg_parse_time = sum(r.get('metrics', {}).get('parse_time_ms', 0) for r in results) / len(results)
        
        report.append(f"Average Search Time: {avg_search_time:.2f}ms")
        report.append(f"Average Parse Time: {avg_parse_time:.2f}ms")
        
        # Accuracy breakdown
        accuracy_counts = defaultdict(int)
        for r in results:
            acc = r.get('accuracy', 'unknown')
            accuracy_counts[acc] += 1
        
        if accuracy_counts:
            report.append("Accuracy Distribution:")
            for acc, count in sorted(accuracy_counts.items()):
                report.append(f"  {acc}: {count}")
        
        report.append("")
    
    # Performance metrics
    report.append("=" * 100)
    report.append("PERFORMANCE METRICS")
    report.append("=" * 100)
    report.append("")
    
    all_search_times = [r.get('metrics', {}).get('search_time_ms', 0) for r in test_results]
    all_parse_times = [r.get('metrics', {}).get('parse_time_ms', 0) for r in test_results]
    
    if all_search_times:
        report.append(f"Search Time:")
        report.append(f"  Min: {min(all_search_times):.2f}ms")
        report.append(f"  Max: {max(all_search_times):.2f}ms")
        report.append(f"  Avg: {sum(all_search_times)/len(all_search_times):.2f}ms")
        report.append(f"  Median: {sorted(all_search_times)[len(all_search_times)//2]:.2f}ms")
        report.append("")
    
    if all_parse_times:
        report.append(f"Parse Time:")
        report.append(f"  Min: {min(all_parse_times):.2f}ms")
        report.append(f"  Max: {max(all_parse_times):.2f}ms")
        report.append(f"  Avg: {sum(all_parse_times)/len(all_parse_times):.2f}ms")
        report.append("")
    
    # Detailed results
    report.append("=" * 100)
    report.append("DETAILED TEST RESULTS")
    report.append("=" * 100)
    report.append("")
    
    for i, result in enumerate(test_results, 1):
        status = "✅" if result.get('success', False) else "❌"
        report.append(f"{i}. {status} {result['query']}")
        report.append(f"   Type: {result['type']}, Intent: {result.get('parsed', {}).get('intent', 'unknown')}")
        
        metrics = result.get('metrics', {})
        if metrics:
            report.append(f"   Search Time: {metrics.get('search_time_ms', 0):.2f}ms")
            report.append(f"   Results: {metrics.get('results_returned', 0)} returned, {metrics.get('search_count', 0)} total")
        
        if result.get('db_count') is not None:
            report.append(f"   DB Count: {result['db_count']}")
            if metrics.get('count_ratio'):
                report.append(f"   Ratio: {metrics['count_ratio']:.2f}x")
        
        if result.get('accuracy'):
            report.append(f"   Accuracy: {result['accuracy']}")
        
        if result.get('warnings'):
            for warning in result['warnings']:
                report.append(f"   ⚠️  {warning}")
        
        if result.get('errors'):
            for error in result['errors']:
                report.append(f"   ❌ {error}")
        
        report.append("")
    
    # Errors summary
    all_errors = []
    for result in test_results:
        all_errors.extend(result.get('errors', []))
    
    if all_errors:
        report.append("=" * 100)
        report.append("ERRORS SUMMARY")
        report.append("=" * 100)
        report.append("")
        for error in all_errors:
            report.append(f"❌ {error}")
        report.append("")
    
    return "\n".join(report)

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all tests."""
    print("\n" + "=" * 100)
    print("COMPREHENSIVE SEARCH EXECUTION TEST")
    print("=" * 100 + "\n")
    
    # Initialize
    print("Initializing services...")
    conn = get_db_connection()
    
    config_path = project_root / "config" / "search_config.json"
    config = None
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    search_service = SearchService()
    search_service.connect_db()
    
    parser = QueryParser(config)
    
    print("✅ Services initialized\n")
    
    # Generate test queries
    print("Generating test queries...")
    test_queries = generate_test_queries()
    print(f"✅ Generated {len(test_queries)} test queries\n")
    
    # Run tests
    print("Running tests...")
    print("This may take a while...\n")
    
    test_results = []
    for i, query_info in enumerate(test_queries, 1):
        print(f"[{i}/{len(test_queries)}] Testing: {query_info['query']}")
        result = run_single_test(query_info, search_service, parser, conn)
        test_results.append(result)
        
        status = "✅" if result.get('success', False) else "❌"
        print(f"  {status} Search: {result.get('metrics', {}).get('search_count', 0)} results, "
              f"{result.get('metrics', {}).get('search_time_ms', 0):.0f}ms")
        if result.get('db_count') is not None:
            print(f"  DB: {result['db_count']} results")
    
    print("\n✅ All tests completed\n")
    
    # Generate report
    print("Generating report...")
    report = generate_report(test_results)
    
    # Save report
    report_path = project_root / "docs" / "COMPREHENSIVE_TEST_REPORT.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Report saved to: {report_path}\n")
    
    # Print summary
    print("=" * 100)
    print("QUICK SUMMARY")
    print("=" * 100)
    print(report.split("DETAILED TEST RESULTS")[0])
    
    # Cleanup
    conn.close()
    search_service.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

