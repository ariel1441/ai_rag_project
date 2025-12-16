"""
IMPROVED Intelligent Field Analysis - Handles Different Naming Conventions

Key improvements:
1. Normalizes field names (snake_case, camelCase, abbreviations)
2. Better data-driven fallback when names don't match
3. Handles non-English field names
4. More robust pattern matching
"""
import psycopg2
from typing import Dict, List, Tuple, Optional
import re
from collections import Counter


class IntelligentFieldAnalyzer:
    """Analyze table fields to suggest optimal embedding weights."""
    
    def __init__(self, cursor):
        self.cursor = cursor
    
    # ============================================================================
    # COLUMN NAME PATTERNS (Universal - works for any table)
    # ============================================================================
    
    # Core semantic words (language-agnostic patterns)
    CRITICAL_WORDS = {
        # Names and titles
        'name', 'title', 'subject', 'topic', 'label', 'nm', 'nm_',
        # Descriptions and content
        'desc', 'description', 'text', 'content', 'body', 'message', 'note', 'remark', 'comment', 'txt',
        # Project/entity identifiers
        'project', 'proj', 'case', 'ticket', 'request', 'order', 'transaction', 'item',
        # User identifiers
        'employee', 'emp', 'contact', 'cont', 'user', 'customer', 'client', 'person', 'agent',
        # Location/area
        'area', 'location', 'region', 'zone', 'district', 'addr', 'address',
        # Summary fields
        'summary', 'overview', 'abstract'
    }
    
    IMPORTANT_WORDS = {
        # Dates and times
        'date', 'dt', 'time', 'tm', 'created', 'updated', 'modified', 'changed', 'closed', 'opened',
        # Contact information
        'email', 'eml', 'phone', 'ph', 'telephone', 'mobile', 'city', 'country',
        # Status and state
        'status', 'stat', 'state', 'phase', 'stage', 'step', 'type', 'typ',
        # Quantities
        'amount', 'quantity', 'count', 'total', 'sum', 'value', 'price', 'cost'
    }
    
    SUPPORTING_WORDS = {
        'detail', 'info', 'data', 'field', 'attribute', 'property', 'flag'
    }
    
    EXCLUDE_WORDS = {
        '_id', '_uuid', '_guid', 'id', 'uuid', 'guid',
        'password', 'secret', 'token', 'key', 'hash',
        'image', 'photo', 'file', 'attachment', 'blob', 'binary'
    }
    
    LOW_PRIORITY_WORDS = {
        'x', 'y', 'lat', 'lon', 'latitude', 'longitude', 'coord',
        'version', 'build', 'revision'
    }
    
    # Abbreviation expansion map
    ABBREV_MAP = {
        'proj': 'project', 'desc': 'description', 'nm': 'name', 'id': 'identifier',
        'num': 'number', 'dt': 'date', 'tm': 'time', 'eml': 'email',
        'ph': 'phone', 'addr': 'address', 'org': 'organization',
        'emp': 'employee', 'cont': 'contact', 'stat': 'status',
        'typ': 'type', 'rem': 'remark', 'cmt': 'comment', 'txt': 'text'
    }
    
    def normalize_field_name(self, column_name: str) -> List[str]:
        """
        Normalize field name to extract meaningful words.
        
        Handles:
        - snake_case: project_name -> ['project', 'name']
        - camelCase: projectName -> ['project', 'name']
        - PascalCase: ProjectName -> ['project', 'name']
        - no_case: projectname -> ['project', 'name'] (if we can detect)
        - Abbreviations: proj_nm -> ['project', 'name']
        """
        name = column_name.lower()
        
        # Check exclude patterns first
        for exclude in self.EXCLUDE_WORDS:
            if exclude in name:
                return []  # Will be excluded
        
        # Replace separators with spaces
        name = name.replace('_', ' ').replace('-', ' ').replace('.', ' ')
        
        # Handle camelCase/PascalCase
        if '_' not in column_name and '-' not in column_name:
            # Insert space before capital letters
            name = re.sub(r'([a-z])([A-Z])', r'\1 \2', column_name).lower()
        
        # Split into words
        words = name.split()
        
        # Expand abbreviations
        expanded_words = []
        for word in words:
            # Check if word is an abbreviation
            if word in self.ABBREV_MAP:
                expanded_words.append(self.ABBREV_MAP[word])
            # Check if word starts with abbreviation pattern
            elif any(word.startswith(abbrev) for abbrev in self.ABBREV_MAP.keys()):
                # Try to match: proj -> project
                for abbrev, full in self.ABBREV_MAP.items():
                    if word.startswith(abbrev):
                        expanded_words.append(full)
                        break
            else:
                expanded_words.append(word)
        
        return expanded_words
    
    def analyze_field_name(self, column_name: str, data_type: str) -> Tuple[float, str]:
        """
        Analyze column name to suggest importance weight.
        
        Returns:
            (weight: float, reason: str)
        """
        name_lower = column_name.lower()
        
        # Check exclude patterns first
        for exclude in self.EXCLUDE_WORDS:
            if exclude in name_lower:
                return (0.0, f"Excluded: contains '{exclude}'")
        
        # Normalize to extract words FIRST (before checking low priority patterns)
        words = self.normalize_field_name(column_name)
        
        if not words:
            # If normalization failed (excluded), return 0
            return (0.0, "Excluded by normalization")
        
        # Check low priority patterns AFTER normalization (exact word match only)
        for pattern in self.LOW_PRIORITY_WORDS:
            # Check if pattern is an exact word match (not substring)
            if any(word == pattern for word in words):
                return (0.5, f"Low priority: exact match '{pattern}'")
        
        # Check for ID suffix
        if name_lower.endswith('_id') or (name_lower.endswith('id') and len(name_lower) > 2):
            descriptive_ids = ['status', 'type', 'reason', 'source', 'priority', 'severity']
            base_name = name_lower.replace('_id', '').replace('id', '')
            if any(desc in base_name for desc in descriptive_ids):
                return (2.0, f"Descriptive ID: {base_name}")
            else:
                return (0.0, "Foreign key ID (excluded)")
        
        # Check words against patterns (EXACT word matching, not substring)
        critical_matched_words = [w for w in words if w in self.CRITICAL_WORDS]
        important_matched_words = [w for w in words if w in self.IMPORTANT_WORDS]
        supporting_matched_words = [w for w in words if w in self.SUPPORTING_WORDS]
        
        critical_matches = len(critical_matched_words)
        important_matches = len(important_matched_words)
        supporting_matches = len(supporting_matched_words)
        
        # Determine weight based on matches
        if critical_matches > 0:
            return (3.0, f"Critical: contains {critical_matches} critical word(s): {critical_matched_words}")
        elif important_matches > 0:
            return (2.0, f"Important: contains {important_matches} important word(s): {important_matched_words}")
        elif supporting_matches > 0:
            return (1.0, f"Supporting: contains {supporting_matches} supporting word(s): {supporting_matched_words}")
        
        # No pattern match - fall back to data type
        if 'text' in data_type.lower() or 'varchar' in data_type.lower() or 'char' in data_type.lower():
            return (1.0, f"Text field (no pattern match): {data_type}")
        elif 'date' in data_type.lower() or 'time' in data_type.lower():
            return (2.0, f"Date/time field: {data_type}")
        else:
            return (0.5, f"Non-text field: {data_type}")
    
    def analyze_data_quality(self, table_name: str, column_name: str, sample_size: int = 1000) -> Dict:
        """
        Analyze actual data to determine importance.
        This is the FALLBACK when field names don't match patterns.
        
        Returns:
            Dict with coverage, uniqueness, diversity, avg_length, and calculated score
        """
        try:
            # Get total row count FIRST (for accurate coverage calculation)
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            total_table_rows = self.cursor.fetchone()[0]
            
            if total_table_rows == 0:
                return {
                    'coverage': 0.0,
                    'uniqueness': 0.0,
                    'diversity': 0.0,
                    'avg_length': 0.0,
                    'score': 0.0
                }
            
            # Get non-null count
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} IS NOT NULL;")
            non_null_count_total = self.cursor.fetchone()[0]
            
            # Get sample data for analysis (non-null values only)
            self.cursor.execute(f"""
                SELECT {column_name}
                FROM {table_name}
                WHERE {column_name} IS NOT NULL
                LIMIT {sample_size * 2}
            """)
            rows = self.cursor.fetchall()
            
            if not rows:
                # No non-null values
                return {
                    'coverage': 0.0,
                    'uniqueness': 0.0,
                    'diversity': 0.0,
                    'avg_length': 0.0,
                    'score': 0.0
                }
            
            # Convert to strings and filter (remove empty strings)
            values = []
            for row in rows:
                if row[0] is not None:
                    value_str = str(row[0]).strip()
                    if value_str:  # Only add non-empty strings
                        values.append(value_str)
            
            if not values:
                return {
                    'coverage': 0.0,
                    'uniqueness': 0.0,
                    'diversity': 0.0,
                    'avg_length': 0.0,
                    'score': 0.0
                }
            
            # Calculate metrics
            # Coverage: non-null rows / total rows
            coverage = non_null_count_total / total_table_rows if total_table_rows > 0 else 0.0
            
            # Uniqueness
            unique_count = len(set(values))
            uniqueness = unique_count / len(values) if len(values) > 0 else 0.0
            
            # Diversity (entropy) - measure of how evenly distributed values are
            value_counts = Counter(values)
            if len(value_counts) > 1:
                total = sum(value_counts.values())
                # Calculate Shannon entropy
                import math
                entropy = -sum((count / total) * math.log2(count / total) for count in value_counts.values())
                # Normalize: max entropy is log2(number of unique values)
                max_entropy = math.log2(len(value_counts)) if len(value_counts) > 1 else 1.0
                diversity = entropy / max_entropy if max_entropy > 0 else 0.0
            else:
                diversity = 0.0  # All same value = no diversity
            
            # Average text length
            avg_length = sum(len(v) for v in values) / len(values) if values else 0.0
            
            # Calculate importance score
            length_factor = min(avg_length / 50.0, 1.0)
            score = (coverage * 0.4) + (uniqueness * 0.3) + (diversity * 0.2) + (length_factor * 0.1)
            
            return {
                'coverage': coverage,
                'uniqueness': uniqueness,
                'diversity': diversity,
                'avg_length': avg_length,
                'score': score
            }
            
        except Exception as e:
            return {
                'coverage': 0.5,
                'uniqueness': 0.5,
                'diversity': 0.5,
                'avg_length': 0.0,
                'score': 0.5,
                'error': str(e)
            }
    
    def analyze_table(self, table_name: str, sample_size: int = 1000) -> Dict:
        """
        Analyze entire table to suggest field weights.
        
        KEY IMPROVEMENT: When field names don't match patterns,
        relies more heavily on data analysis.
        """
        # Get table schema
        self.cursor.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))
        
        columns = []
        for row in self.cursor.fetchall():
            columns.append({
                'name': row[0],
                'type': row[1],
                'nullable': row[2] == 'YES'
            })
        
        if not columns:
            return {'error': f'Table {table_name} not found or has no columns'}
        
        # Get total row count
        total_rows = self.get_total_row_count(table_name)
        actual_sample_size = min(sample_size, total_rows) if total_rows > 0 else sample_size
        
        # Analyze each column
        results = []
        for col in columns:
            col_name = col['name']
            col_type = col['type']
            
            # Name-based analysis
            name_weight, name_reason = self.analyze_field_name(col_name, col_type)
            
            # Skip if excluded
            if name_weight == 0.0:
                results.append({
                    'column': col_name,
                    'type': col_type,
                    'name_weight': 0.0,
                    'name_reason': name_reason,
                    'data_analysis': None,
                    'final_weight': 0.0,
                    'recommendation': 'EXCLUDE'
                })
                continue
            
            # Data-based analysis
            data_analysis = self.analyze_data_quality(table_name, col_name, actual_sample_size)
            
            # IMPROVED: Adjust weight combination based on name match quality
            # If name doesn't match patterns well (weight < 2.0), trust data more
            if name_weight < 2.0:
                # Name didn't match well - trust data more (40% name, 60% data)
                data_weight = 1.0 + (data_analysis['score'] * 2.0)
                combined_weight = (name_weight * 0.4) + (data_weight * 0.6)
                name_reason += " (low name match - using data-driven analysis)"
            else:
                # Name matched well - trust name more (70% name, 30% data)
                data_weight = 1.0 + (data_analysis['score'] * 2.0)
                combined_weight = (name_weight * 0.7) + (data_weight * 0.3)
            
            # Round to final weight
            if name_weight >= 3.0:
                if combined_weight >= 2.3:
                    final_weight = 3.0
                elif combined_weight >= 1.5:
                    final_weight = 2.0
                else:
                    final_weight = 1.0
            elif name_weight >= 2.0:
                if combined_weight >= 2.0:
                    final_weight = 2.0
                elif combined_weight >= 1.2:
                    final_weight = 1.0
                else:
                    final_weight = 0.5
            else:
                # Name didn't match - data-driven
                if combined_weight >= 2.0:
                    final_weight = 2.0
                elif combined_weight >= 1.5:
                    final_weight = 1.0
                elif combined_weight >= 0.8:
                    final_weight = 0.5
                else:
                    final_weight = 0.0
            
            # Determine recommendation
            if final_weight >= 2.5:
                recommendation = 'CRITICAL (3.0x)'
            elif final_weight >= 1.5:
                recommendation = 'IMPORTANT (2.0x)'
            elif final_weight >= 0.8:
                recommendation = 'SUPPORTING (1.0x)'
            else:
                recommendation = 'LOW (0.5x)'
            
            results.append({
                'column': col_name,
                'type': col_type,
                'name_weight': name_weight,
                'name_reason': name_reason,
                'data_analysis': data_analysis,
                'final_weight': final_weight,
                'recommendation': recommendation
            })
        
        # Sort by final weight
        results.sort(key=lambda x: x['final_weight'], reverse=True)
        
        return {
            'table_name': table_name,
            'total_rows': total_rows,
            'sample_size': actual_sample_size,
            'columns_analyzed': len([r for r in results if r['final_weight'] > 0]),
            'columns_excluded': len([r for r in results if r['final_weight'] == 0]),
            'results': results
        }
    
    def get_total_row_count(self, table_name: str) -> int:
        """Get total row count for a table."""
        try:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            return self.cursor.fetchone()[0]
        except:
            return 0
    
    def generate_weight_config(self, analysis_result: Dict) -> Dict:
        """Generate weight configuration from analysis results."""
        weights = {
            '3.0x': [],
            '2.0x': [],
            '1.0x': [],
            '0.5x': [],
            'exclude': []
        }
        
        for result in analysis_result['results']:
            col_name = result['column']
            final_weight = result['final_weight']
            
            if final_weight == 0.0:
                weights['exclude'].append(col_name)
            elif final_weight >= 2.5:
                weights['3.0x'].append(col_name)
            elif final_weight >= 1.5:
                weights['2.0x'].append(col_name)
            elif final_weight >= 0.8:
                weights['1.0x'].append(col_name)
            else:
                weights['0.5x'].append(col_name)
        
        return weights


def analyze_table_fields(cursor, table_name: str, sample_size: int = 1000) -> Dict:
    """Main function to analyze table fields."""
    analyzer = IntelligentFieldAnalyzer(cursor)
    analysis = analyzer.analyze_table(table_name, sample_size)
    
    if 'error' in analysis:
        return analysis
    
    weights = analyzer.generate_weight_config(analysis)
    
    return {
        'analysis': analysis,
        'weights': weights
    }


if __name__ == "__main__":
    # Example usage
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5433")),
        database=os.getenv("POSTGRES_DATABASE", "ai_requests_db"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    
    cursor = conn.cursor()
    
    result = analyze_table_fields(cursor, "requests", sample_size=1000)
    
    print("=" * 80)
    print("IMPROVED INTELLIGENT FIELD ANALYSIS")
    print("=" * 80)
    print(f"Table: {result['analysis']['table_name']}")
    print(f"Total Rows: {result['analysis']['total_rows']:,}")
    print()
    
    print("Weight Suggestions:")
    print("-" * 80)
    print(f"3.0x (Critical): {len(result['weights']['3.0x'])} fields")
    for field in result['weights']['3.0x'][:10]:
        field_analysis = next((r for r in result['analysis']['results'] if r['column'] == field), None)
        if field_analysis:
            reason = field_analysis.get('name_reason', 'N/A')
            coverage = field_analysis.get('data_analysis', {}).get('coverage', 0) * 100
            print(f"  - {field:30s} Coverage: {coverage:.1f}% | {reason[:50]}")
    
    print()
    print(f"2.0x (Important): {len(result['weights']['2.0x'])} fields")
    print(f"1.0x (Supporting): {len(result['weights']['1.0x'])} fields")
    print(f"0.5x (Low): {len(result['weights']['0.5x'])} fields")
    print(f"Excluded: {len(result['weights']['exclude'])} fields")
    
    cursor.close()
    conn.close()

