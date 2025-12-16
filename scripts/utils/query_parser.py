"""
Query Parser - Understands user intent and extracts entities.

This is GENERAL logic - can be reused for any client.
Client-specific: patterns, field mappings (in config).

Enhanced with:
- Date extraction (relative and absolute dates)
- Urgency detection
- Project vs request entity detection
- Answer retrieval detection
- Enhanced query type detection
"""
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

class QueryParser:
    """
    Parses natural language queries to understand intent.
    
    GENERAL (reusable):
    - Intent detection (person, project, type, etc.)
    - Entity extraction (names, IDs, dates)
    - Query type classification
    
    CLIENT-SPECIFIC (config):
    - Hebrew patterns ("מא", "של", etc.)
    - Field name mappings (Hebrew → English)
    - Query patterns
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize with optional config.
        If no config, uses defaults (can be overridden per client).
        Supports both flat config (default) and nested JSON config.
        """
        if config is None:
            self.config = self._default_config()
        else:
            # Transform JSON config to flat format if needed
            self.config = self._normalize_config(config)
    
    def _normalize_config(self, config: Dict) -> Dict:
        """
        Normalize config from JSON format to flat format expected by parser.
        Handles both nested JSON structure and flat structure.
        """
        normalized = {}
        
        # Check if it's nested JSON format (has query_patterns)
        if 'query_patterns' in config:
            # Extract patterns from nested structure
            query_patterns = config.get('query_patterns', {})
            
            # Person patterns
            if 'person_queries' in query_patterns:
                normalized['person_patterns'] = query_patterns['person_queries'].get('patterns', [])
                normalized['person_fields'] = query_patterns['person_queries'].get('target_fields', [])
            else:
                normalized['person_patterns'] = []
                normalized['person_fields'] = []
            
            # Project patterns
            if 'project_queries' in query_patterns:
                normalized['project_patterns'] = query_patterns['project_queries'].get('patterns', [])
                normalized['project_fields'] = query_patterns['project_queries'].get('target_fields', [])
            else:
                normalized['project_patterns'] = []
                normalized['project_fields'] = []
            
            # Type patterns
            if 'type_queries' in query_patterns:
                normalized['type_patterns'] = query_patterns['type_queries'].get('patterns', [])
            else:
                normalized['type_patterns'] = []
            
            # Status patterns
            if 'status_queries' in query_patterns:
                normalized['status_patterns'] = query_patterns['status_queries'].get('patterns', [])
            else:
                normalized['status_patterns'] = []
            
            # Date patterns
            if 'date_queries' in query_patterns:
                normalized['date_patterns'] = query_patterns['date_queries'].get('patterns', [])
            else:
                normalized['date_patterns'] = []
            
            # Field mappings
            normalized['field_mappings'] = config.get('field_mappings', {})
            
        else:
            # Already in flat format, use as-is (but ensure all keys exist)
            normalized = config.copy()
            # Ensure all required keys exist with defaults
            defaults = self._default_config()
            for key, value in defaults.items():
                if key not in normalized:
                    normalized[key] = value
        
        return normalized
    
    def _default_config(self) -> Dict:
        """Default config - can be overridden per client."""
        return {
            # Hebrew patterns that indicate person queries
            'person_patterns': ['מא', 'של', 'על ידי', 'מאת', 'מ-'],
            
            # Hebrew patterns that indicate project queries
            'project_patterns': ['פרויקט', 'פרויקטים', 'project'],
            
            # Hebrew patterns that indicate type queries
            'type_patterns': ['מסוג', 'סוג', 'type'],
            
            # Hebrew patterns that indicate status queries
            'status_patterns': ['סטטוס', 'status', 'מצב'],
            
            # Field name mappings (Hebrew → English)
            'field_mappings': {
                'מסוג': 'requesttypeid',
                'סוג': 'requesttypeid',
                'סטטוס': 'requeststatusid',
                'מצב': 'requeststatusid',
                'פרויקט': 'projectname',
                'שם פרויקט': 'projectname',
                'מאת': 'createdby',
                'מא': 'updatedby',  # "פניות מאX" = updatedby
                'של': 'updatedby',  # "פניות של X" = updatedby
                'על ידי': 'updatedby',
                'אחראי': 'responsibleemployeename',
                'אחראית': 'responsibleemployeename',
            },
            
            # Person-related fields (for person queries)
            'person_fields': ['updatedby', 'createdby', 'responsibleemployeename', 
                            'contactfirstname', 'contactlastname'],
            
            # Project-related fields
            'project_fields': ['projectname', 'projectdesc'],
            
            # Date-related patterns
            'date_patterns': ['מ-', 'עד', 'מיום', 'לפני', 'אחרי', 'בין', 'אחרון', 'אחרונים', 'השבוע', 'החודש'],
            
            # Urgency-related patterns
            'urgency_patterns': ['דחוף', 'דחופה', 'דחופות', 'דחיפות', 'תאריך יעד', 'deadline', 'קרוב', 'דורש תשובה'],
            
            # Project vs request detection patterns
            'project_entity_patterns': ['פרויקט', 'פרויקטים', 'project', 'projects'],
            'request_entity_patterns': ['פניות', 'בקשות', 'requests', 'request'],
            
            # Answer retrieval patterns
            'answer_retrieval_patterns': ['מענה', 'תשובה', 'answer', 'response', 'מענה דומה', 'תשובה דומה'],
        }
    
    def parse(self, query: str) -> Dict:
        """
        Parse query and return structured information.
        
        Returns:
        {
            'intent': 'person' | 'project' | 'type' | 'status' | 'general',
            'entities': {
                'person_name': 'אור גלילי',
                'project_name': '...',
                'type_id': 4,
                'status_id': 1,
                'date_range': {'start': date, 'end': date, 'days': int},
                'urgency': bool,
                'request_id': str,  # For similar queries
            },
            'target_fields': ['updatedby', 'createdby'],  # Which fields to search
            'query_type': 'find' | 'count' | 'summarize' | 'similar' | 'urgent' | 'answer_retrieval',
            'entity_type': 'requests' | 'projects' | None,  # What entity user is asking about
            'filters': {...},  # SQL filters
            'original_query': query
        }
        """
        query_lower = query.lower()
        result = {
            'intent': 'general',
            'entities': {},
            'target_fields': [],
            'query_type': 'find',
            'entity_type': None,  # 'requests' or 'projects'
            'filters': {},
            'original_query': query
        }
        
        # Detect entity type (projects vs requests) - do this first as it affects query type
        result['entity_type'] = self._detect_entity_type(query_lower)
        
        # Detect query type (enhanced with urgency and answer retrieval)
        result['query_type'] = self._detect_query_type(query_lower, result['entity_type'])
        
        # Detect urgency (can be combined with other query types)
        result['entities']['urgency'] = self._detect_urgency(query_lower)
        if result['entities']['urgency']:
            # If urgency detected, mark query type as urgent (or combine with existing)
            if result['query_type'] == 'find':
                result['query_type'] = 'urgent'
        
        # Detect answer retrieval
        if self._detect_answer_retrieval(query_lower):
            result['query_type'] = 'answer_retrieval'
            # Extract request ID if present
            request_id = self._extract_request_id(query)
            if request_id:
                result['entities']['request_id'] = request_id
        
        # Detect intent
        result['intent'] = self._detect_intent(query_lower)
        
        # Extract date entities (can be combined with any intent)
        date_info = self._extract_date_entities(query, query_lower)
        if date_info:
            result['entities']['date_range'] = date_info
            # Add date filters
            if 'start' in date_info:
                result['filters']['date_start'] = date_info['start']
            if 'end' in date_info:
                result['filters']['date_end'] = date_info['end']
            if 'days' in date_info:
                result['filters']['days_back'] = date_info['days']
        
        # Extract request ID for similar queries FIRST (before intent extraction)
        # This prevents wrong entity extraction for similar queries
        if result['query_type'] == 'similar':
            request_id = self._extract_request_id(query)
            if request_id:
                result['entities']['request_id'] = request_id
                # For similar queries, set intent to 'general' to avoid wrong entity extraction
                result['intent'] = 'general'
                # Clear any wrong entities that might have been set
                if 'person_name' in result['entities']:
                    del result['entities']['person_name']
                if 'project_name' in result['entities']:
                    del result['entities']['project_name']
        
        # Extract entities based on intent (skip if query_type is similar/answer_retrieval)
        # BUT: Also extract other entities that might be present (for AND logic)
        if result['query_type'] not in ['similar', 'answer_retrieval']:
            # Extract primary entity based on intent
            if result['intent'] == 'person':
                person_name = self._extract_person_name(query, query_lower)
                if person_name:
                    result['entities']['person_name'] = person_name
                    result['target_fields'] = self.config.get('person_fields', [])
            
            elif result['intent'] == 'project':
                project_name = self._extract_project_name(query, query_lower)
                if project_name:
                    result['entities']['project_name'] = project_name
                    result['target_fields'] = self.config.get('project_fields', [])
            
            elif result['intent'] == 'type':
                type_id = self._extract_type_id(query, query_lower)
                if type_id:
                    result['entities']['type_id'] = type_id
                    result['filters']['requesttypeid'] = type_id
            
            elif result['intent'] == 'status':
                status_id = self._extract_status_id(query, query_lower)
                if status_id:
                    result['entities']['status_id'] = status_id
                    result['filters']['requeststatusid'] = status_id
            
            # ALSO extract other entities that might be present (for AND logic with multiple entities)
            # This allows queries like "פניות מאור גלילי מסוג 4" to extract both person_name AND type_id
            # Extract type_id if present (regardless of primary intent)
            if 'type_id' not in result['entities']:
                type_id = self._extract_type_id(query, query_lower)
                if type_id:
                    result['entities']['type_id'] = type_id
                    result['filters']['requesttypeid'] = type_id
            
            # Extract status_id if present (regardless of primary intent)
            if 'status_id' not in result['entities']:
                status_id = self._extract_status_id(query, query_lower)
                if status_id:
                    result['entities']['status_id'] = status_id
                    result['filters']['requeststatusid'] = status_id
            
            # Extract person_name if present (regardless of primary intent, but only if not already extracted)
            if 'person_name' not in result['entities'] and result['intent'] != 'person':
                person_name = self._extract_person_name(query, query_lower)
                if person_name:
                    result['entities']['person_name'] = person_name
                    # Don't override target_fields if already set
            
            # Extract project_name if present (regardless of primary intent, but only if not already extracted)
            if 'project_name' not in result['entities'] and result['intent'] != 'project':
                project_name = self._extract_project_name(query, query_lower)
                if project_name:
                    result['entities']['project_name'] = project_name
                    # Don't override target_fields if already set
        
        return result
    
    def _detect_query_type(self, query_lower: str, entity_type: Optional[str] = None) -> str:
        """
        Detect if query is asking to find, count, summarize, etc.
        
        Args:
            query_lower: Lowercase query
            entity_type: 'requests' or 'projects' or None
            
        Returns:
            Query type: 'find', 'count', 'summarize', 'similar', 'urgent', 'answer_retrieval'
        """
        # Check for answer retrieval first (most specific)
        if self._detect_answer_retrieval(query_lower):
            return 'answer_retrieval'
        
        # Check for similar queries
        if any(word in query_lower for word in ['דומה', 'דומות', 'כמו', 'similar', 'like']):
            return 'similar'
        
        # Check for count queries
        if any(word in query_lower for word in ['כמה', 'מספר', 'count', 'how many']):
            return 'count'
        
        # Check for summarize queries
        if any(word in query_lower for word in ['סיכום', 'תקציר', 'סקירה', 'summarize', 'summary', 'overview']):
            return 'summarize'
        
        # Check for list queries (explicit request for all)
        if any(phrase in query_lower for phrase in ['תביא לי את כל', 'הצג את כל', 'תן לי רשימה', 'כל ה', 'all the']):
            return 'find'  # But with list intent
        
        # Default to find
        return 'find'
    
    def _detect_intent(self, query_lower: str) -> str:
        """Detect query intent: person, project, type, status, or general."""
        # Check for person patterns FIRST (most specific)
        if any(pattern in query_lower for pattern in self.config['person_patterns']):
            return 'person'
        
        # Check for project patterns
        if any(pattern in query_lower for pattern in self.config['project_patterns']):
            return 'project'
        
        # Check for type patterns
        if any(pattern in query_lower for pattern in self.config['type_patterns']):
            return 'type'
        
        # Check for status patterns
        if any(pattern in query_lower for pattern in self.config['status_patterns']):
            return 'status'
        
        # Check if query looks like a person name (2+ Hebrew words)
        # BUT only if it contains person-related context words
        # AND NOT if it contains urgency/date/project patterns (those take priority)
        hebrew_words = re.findall(r'[\u0590-\u05FF]+', query_lower)
        if len(hebrew_words) >= 2:
            # Check for person-related context words
            person_context = ['פניות', 'בקשות', 'מא', 'של', 'מ-', 'יש', 'כמה']
            has_person_context = any(word in query_lower for word in person_context)
            
            # Exclude if it's clearly an urgency/date/project query
            urgency_words = ['דחופות', 'דחופה', 'דחוף', 'דחיפות']
            has_urgency = any(word in query_lower for word in urgency_words)
            
            # Only treat as person if there's person-related context AND not urgency
            # This prevents "בקשות דחופות" from being detected as person
            if has_person_context and not has_urgency:
                return 'person'
        
        return 'general'
    
    def _extract_person_name(self, query: str, query_lower: str) -> Optional[str]:
        """Extract person name from query."""
        # Stop words that indicate end of person name (type/status patterns)
        # These patterns indicate the person name has ended and another entity starts
        stop_patterns = ['מסוג', 'בסטטוס', 'סטטוס', 'type', 'status', 'מ-', 'עד', 'מיום', 'שחדרו', 'שחדר']
        
        # Pattern: "פניות מא X" or "פניות של X" or "פניות מאX" (if X starts with Hebrew)
        for pattern in self.config['person_patterns']:
            # Try to find pattern followed by space and Hebrew word
            # Pattern 1: "מא אור" (pattern + space + name) - BEST CASE
            pattern_with_space = pattern + r'\s+([\u0590-\u05FF]+(?:\s+[\u0590-\u05FF]+)*)'
            match = re.search(pattern_with_space, query_lower)
            if match:
                name = match.group(1)
                # Stop at type/status patterns
                for stop in stop_patterns:
                    if stop in name:
                        name = name.split(stop)[0].strip()
                        break
                # Remove common words
                name = re.sub(r'^(פניות|בקשות|requests?)\s+', '', name, flags=re.IGNORECASE)
                if name.strip():
                    return name.strip()
            
            # Pattern 2: "מאX" where X is Hebrew (pattern directly before Hebrew, no space)
            # This handles "מאור" -> should extract "אור" (keep the "א" from the name)
            pattern_idx = query_lower.find(pattern)
            if pattern_idx != -1:
                after_idx = pattern_idx + len(pattern)
                if after_idx < len(query):
                    next_char = query[after_idx]
                    # If no space after pattern, it's "מאX" format
                    if next_char != ' ' and ('\u0590' <= next_char <= '\u05FF'):
                        # Special case: "מא" pattern where the "א" is part of the name
                        # In "מאור", pattern "מא" is at positions 6-7, but the name "אור" starts at position 7
                        # So we need to extract from position idx+1 (the "א"), not idx+2 (after "מא")
                        if pattern == 'מא' and pattern_idx + 1 < len(query):
                            char_after_mem = query[pattern_idx + 1]  # Should be "א" in "מאור"
                            if char_after_mem == 'א':
                                # This is "מא" + name starting with "א" (e.g., "מאור")
                                # Extract name starting from the "א" (position idx+1)
                                name_start = pattern_idx + 1
                                # Find end of Hebrew word/name
                                name_end = name_start
                                while name_end < len(query) and ('\u0590' <= query[name_end] <= '\u05FF'):
                                    name_end += 1
                                # Get the rest of the text after this word
                                after_name = query[name_end:].strip()
                                # Extract all Hebrew words (the name + any following words)
                                all_text_after = query[name_start:].strip()
                                # Stop at type/status patterns
                                for stop in stop_patterns:
                                    if stop in all_text_after:
                                        all_text_after = all_text_after.split(stop)[0].strip()
                                        break
                                # Remove common words
                                all_text_after = re.sub(r'^(פניות|בקשות|requests?)\s+', '', all_text_after, flags=re.IGNORECASE)
                                hebrew_words = re.findall(r'[\u0590-\u05FF]+', all_text_after)
                                if hebrew_words:
                                    return ' '.join(hebrew_words)
                        
                        # Regular case: pattern + Hebrew word (no special "א" handling needed)
                        # Get text after pattern
                        after_pattern = query[after_idx:].strip()
                        # Stop at type/status patterns
                        for stop in stop_patterns:
                            if stop in after_pattern:
                                after_pattern = after_pattern.split(stop)[0].strip()
                                break
                        # Remove common words
                        after_pattern = re.sub(r'^(פניות|בקשות|requests?)\s+', '', after_pattern, flags=re.IGNORECASE)
                        # Extract Hebrew words
                        hebrew_words = re.findall(r'[\u0590-\u05FF]+', after_pattern)
                        if hebrew_words:
                            return ' '.join(hebrew_words)
        
        # Pattern 3: Handle "יש מיניב" or "יש מאX" - "יש" followed by name or pattern+name
        # This handles "כמה פניות יש מיניב ליבוביץ?" and "כמה פניות יש מאוקסנה כלפון?"
        if 'יש' in query_lower:
            יש_idx = query_lower.find('יש')
            if יש_idx != -1:
                after_יש = query[יש_idx + 2:].strip()  # +2 for "יש"
                # Remove question marks
                after_יש = re.sub(r'[?؟\s]+$', '', after_יש)
                
                # Check if there's a pattern after "יש"
                for pattern in self.config['person_patterns']:
                    if after_יש.startswith(pattern):
                        # "יש מאX" or "יש מ-X"
                        pattern_end = len(pattern)
                        if pattern_end < len(after_יש):
                            name_part = after_יש[pattern_end:].strip()
                            # Stop at type/status patterns
                            for stop in stop_patterns:
                                if stop in name_part:
                                    name_part = name_part.split(stop)[0].strip()
                                    break
                            # Remove common words
                            name_part = re.sub(r'^(פניות|בקשות|requests?)\s+', '', name_part, flags=re.IGNORECASE)
                            hebrew_words = re.findall(r'[\u0590-\u05FF]+', name_part)
                            if len(hebrew_words) >= 2:
                                # Filter out common words
                                filtered = [w for w in hebrew_words if w not in ['פניות', 'בקשות', 'תביא', 'הראה', 'מצא', 'כמה', 'יש']]
                                if len(filtered) >= 2:
                                    # Special case: if first word starts with "מ" and pattern was "מא", 
                                    # it might be "מא מיניב" -> "מיניב", but we want "יניב"
                                    # Actually, if there's a space, pattern 1 already handled it
                                    # Here it's "מאX" without space, so keep as-is
                                    return ' '.join(filtered)
                
                # No pattern found, just extract Hebrew words after "יש"
                # Stop at type/status patterns
                for stop in stop_patterns:
                    if stop in after_יש:
                        after_יש = after_יש.split(stop)[0].strip()
                        break
                hebrew_words = re.findall(r'[\u0590-\u05FF]+', after_יש)
                if len(hebrew_words) >= 2:
                    # Filter out common words
                    filtered = [w for w in hebrew_words if w not in ['פניות', 'בקשות', 'תביא', 'הראה', 'מצא', 'כמה', 'יש', 'מא', 'של', 'מ-']]
                    if len(filtered) >= 2:
                        # Special handling: if first word starts with "מ" and is followed by another word,
                        # it might be "מיניב" when the actual name is "יניב" (the "מ" is a prefix)
                        # Check if removing "מ" from first word makes sense
                        first_word = filtered[0]
                        if first_word.startswith('מ') and len(first_word) > 1:
                            # Try without "מ" prefix: "מיניב" -> "יניב"
                            name_without_mem = first_word[1:]  # Remove first char "מ"
                            # If the result is a valid Hebrew word (2+ chars), use it
                            if len(name_without_mem) >= 2:
                                filtered[0] = name_without_mem
                        return ' '.join(filtered)
        
        # Pattern 4: Handle "תביא לי פניות מ-X" or "תביא לי פניות מאX"
        if any(word in query_lower for word in ['תביא', 'הראה', 'מצא']):
            for pattern in self.config['person_patterns']:
                pattern_idx = query_lower.find(pattern)
                if pattern_idx != -1:
                    after_idx = pattern_idx + len(pattern)
                    if after_idx < len(query):
                        # Special case for "מא" + name starting with "א" (same as Pattern 2)
                        if pattern == 'מא' and pattern_idx + 1 < len(query):
                            char_after_mem = query[pattern_idx + 1]
                            if char_after_mem == 'א':
                                name_start = pattern_idx + 1
                                all_text_after = query[name_start:].strip()
                                # Stop at type/status patterns
                                for stop in stop_patterns:
                                    if stop in all_text_after:
                                        all_text_after = all_text_after.split(stop)[0].strip()
                                        break
                                all_text_after = re.sub(r'^(פניות|בקשות|requests?|לי|תביא|הראה|מצא)\s+', '', all_text_after, flags=re.IGNORECASE)
                                hebrew_words = re.findall(r'[\u0590-\u05FF]+', all_text_after)
                                if len(hebrew_words) >= 2:
                                    filtered = [w for w in hebrew_words if w not in ['פניות', 'בקשות', 'תביא', 'הראה', 'מצא', 'כמה', 'יש', 'לי']]
                                    if len(filtered) >= 2:
                                        return ' '.join(filtered)
                        
                        after_pattern = query[after_idx:].strip()
                        # Stop at type/status patterns
                        for stop in stop_patterns:
                            if stop in after_pattern:
                                after_pattern = after_pattern.split(stop)[0].strip()
                                break
                        # Remove common words
                        after_pattern = re.sub(r'^(פניות|בקשות|requests?|לי|תביא|הראה|מצא)\s+', '', after_pattern, flags=re.IGNORECASE)
                        hebrew_words = re.findall(r'[\u0590-\u05FF]+', after_pattern)
                        if len(hebrew_words) >= 2:
                            # Filter out common words
                            filtered = [w for w in hebrew_words if w not in ['פניות', 'בקשות', 'תביא', 'הראה', 'מצא', 'כמה', 'יש', 'לי']]
                            if len(filtered) >= 2:
                                # Check if first word starts with "מ" and remove it if it's a prefix
                                first_word = filtered[0]
                                if first_word.startswith('מ') and len(first_word) > 1:
                                    filtered[0] = first_word[1:]
                                return ' '.join(filtered)
        
        # Fallback: Extract any 2+ Hebrew words (might be a name)
        # But first, stop at type/status patterns
        query_for_fallback = query
        for stop in stop_patterns:
            if stop in query_for_fallback:
                query_for_fallback = query_for_fallback.split(stop)[0].strip()
                break
        hebrew_words = re.findall(r'[\u0590-\u05FF]+', query_for_fallback)
        if len(hebrew_words) >= 2:
            # Remove common query words
            filtered = [w for w in hebrew_words if w not in ['פניות', 'בקשות', 'תביא', 'הראה', 'מצא', 'כמה', 'יש', 'מא', 'של', 'מ-', 'לי']]
            if len(filtered) >= 2:
                # Check if first word starts with "מ" - might be a prefix
                first_word = filtered[0]
                if first_word.startswith('מ') and len(first_word) > 1:
                    # Try without "מ" prefix: "מיניב" -> "יניב"
                    name_without_mem = first_word[1:]  # Remove first char "מ"
                    if len(name_without_mem) >= 2:
                        filtered[0] = name_without_mem
                return ' '.join(filtered)
        
        return None
    
    def _extract_project_name(self, query: str, query_lower: str) -> Optional[str]:
        """Extract project name from query."""
        for pattern in self.config['project_patterns']:
            if pattern in query_lower:
                pattern_idx = query_lower.find(pattern)
                if pattern_idx != -1:
                    after_pattern = query[pattern_idx + len(pattern):].strip()
                    if after_pattern:
                        return after_pattern.strip()
        return None
    
    def _extract_type_id(self, query: str, query_lower: str) -> Optional[int]:
        """Extract type ID from query."""
        # Look for "מסוג 4" or "type 4"
        type_match = re.search(r'(מסוג|סוג|type)\s*(\d+)', query_lower)
        if type_match:
            return int(type_match.group(2))
        
        # Look for just a number after type pattern
        type_match = re.search(r'(\d+)', query)
        if type_match and any(p in query_lower for p in self.config['type_patterns']):
            return int(type_match.group(1))
        
        return None
    
    def _extract_status_id(self, query: str, query_lower: str) -> Optional[int]:
        """Extract status ID from query."""
        status_match = re.search(r'(סטטוס|status|מצב)\s*(\d+)', query_lower)
        if status_match:
            return int(status_match.group(2))
        return None
    
    def _detect_entity_type(self, query_lower: str) -> Optional[str]:
        """
        Detect what entity type user is asking about: 'projects' or 'requests'.
        
        Returns:
            'projects' if query mentions projects, 'requests' if mentions requests, None if unclear
        """
        project_patterns = self.config.get('project_entity_patterns', ['פרויקט', 'פרויקטים'])
        request_patterns = self.config.get('request_entity_patterns', ['פניות', 'בקשות'])
        
        has_project = any(pattern in query_lower for pattern in project_patterns)
        has_request = any(pattern in query_lower for pattern in request_patterns)
        
        # If explicitly mentions projects, return 'projects'
        if has_project and not has_request:
            return 'projects'
        # If explicitly mentions requests or both, default to 'requests'
        elif has_request:
            return 'requests'
        # If neither, return None (will default to requests in processing)
        return None
    
    def _detect_urgency(self, query_lower: str) -> bool:
        """
        Detect if query is about urgency/priority.
        
        Returns:
            True if urgency detected, False otherwise
        """
        urgency_patterns = self.config.get('urgency_patterns', [
            'דחוף', 'דחופה', 'דחופות', 'דחיפות', 
            'תאריך יעד', 'deadline', 'קרוב', 'דורש תשובה'
        ])
        return any(pattern in query_lower for pattern in urgency_patterns)
    
    def _detect_answer_retrieval(self, query_lower: str) -> bool:
        """
        Detect if user wants to retrieve answer from similar request.
        
        Returns:
            True if answer retrieval detected, False otherwise
        """
        answer_patterns = self.config.get('answer_retrieval_patterns', [
            'מענה', 'תשובה', 'answer', 'response'
        ])
        
        # Check if query contains answer pattern + similar/request ID
        has_answer_pattern = any(pattern in query_lower for pattern in answer_patterns)
        has_similar = any(word in query_lower for word in ['דומה', 'דומה ל', 'similar', 'like'])
        has_request_id = bool(re.search(r'\d{9}', query_lower))  # 9-digit request ID
        
        # Answer retrieval: has answer pattern AND (similar OR request ID)
        return has_answer_pattern and (has_similar or has_request_id)
    
    def _extract_request_id(self, query: str) -> Optional[str]:
        """
        Extract request ID from query (9-digit number).
        
        Returns:
            Request ID as string if found, None otherwise
        """
        # Look for 9-digit number (request ID format)
        match = re.search(r'\b(\d{9})\b', query)
        if match:
            return match.group(1)
        return None
    
    def _extract_date_entities(self, query: str, query_lower: str) -> Optional[Dict]:
        """
        Extract date-related entities from query.
        
        Handles:
        - Relative dates: "10 ימים אחרונים", "השבוע האחרון", "החודש האחרון"
        - Date ranges: "מ-1/1/2024 עד 31/1/2024"
        - Single dates: "מ-1/1/2024", "עד היום"
        
        Returns:
            Dict with date information:
            {
                'start': datetime or None,
                'end': datetime or None,
                'days': int or None,  # Days back from today
                'type': 'relative' | 'absolute' | 'range'
            }
        """
        date_info = {}
        today = datetime.now().date()
        
        # Pattern 1: Relative dates - "X ימים אחרונים" or "X ימים אחרונות"
        days_match = re.search(r'(\d+)\s*ימים?\s*(אחרונים?|אחרונות?)', query_lower)
        if days_match:
            days = int(days_match.group(1))
            date_info['days'] = days
            date_info['start'] = today - timedelta(days=days)
            date_info['end'] = today
            date_info['type'] = 'relative'
            return date_info
        
        # Pattern 2: "השבוע האחרון" or "השבוע האחרונה"
        if 'השבוע האחרון' in query_lower or 'השבוע האחרונה' in query_lower:
            date_info['days'] = 7
            date_info['start'] = today - timedelta(days=7)
            date_info['end'] = today
            date_info['type'] = 'relative'
            return date_info
        
        # Pattern 3: "החודש האחרון" or "החודש האחרונה"
        if 'החודש האחרון' in query_lower or 'החודש האחרונה' in query_lower:
            date_info['days'] = 30
            date_info['start'] = today - timedelta(days=30)
            date_info['end'] = today
            date_info['type'] = 'relative'
            return date_info
        
        # Pattern 4: "אחרון" or "אחרונים" without number (default to 7 days)
        if 'אחרון' in query_lower or 'אחרונים' in query_lower:
            # Check if there's a number before it
            num_match = re.search(r'(\d+)\s*(אחרון|אחרונים)', query_lower)
            if num_match:
                days = int(num_match.group(1))
            else:
                days = 7  # Default to last week
            date_info['days'] = days
            date_info['start'] = today - timedelta(days=days)
            date_info['end'] = today
            date_info['type'] = 'relative'
            return date_info
        
        # Pattern 5: Date range "מ-X עד Y" or "from X to Y"
        # Look for date patterns: DD/MM/YYYY or DD-MM-YYYY
        date_pattern = r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})'
        dates = re.findall(date_pattern, query)
        
        if len(dates) >= 2:
            # Two dates found - range
            try:
                start_date = datetime(int(dates[0][2]), int(dates[0][1]), int(dates[0][0])).date()
                end_date = datetime(int(dates[1][2]), int(dates[1][1]), int(dates[1][0])).date()
                date_info['start'] = start_date
                date_info['end'] = end_date
                date_info['type'] = 'range'
                return date_info
            except ValueError:
                pass
        
        # Pattern 6: Single date with "מ-" or "from"
        if 'מ-' in query_lower or 'from' in query_lower:
            if dates:
                try:
                    start_date = datetime(int(dates[0][2]), int(dates[0][1]), int(dates[0][0])).date()
                    date_info['start'] = start_date
                    date_info['end'] = today
                    date_info['type'] = 'absolute'
                    return date_info
                except ValueError:
                    pass
        
        # Pattern 7: "עד היום" or "until today"
        if 'עד היום' in query_lower or 'until today' in query_lower:
            if dates:
                try:
                    end_date = datetime(int(dates[0][2]), int(dates[0][1]), int(dates[0][0])).date()
                    date_info['start'] = None  # No start limit
                    date_info['end'] = end_date
                    date_info['type'] = 'absolute'
                    return date_info
                except ValueError:
                    pass
        
        # No date information found
        return None


def parse_query(query: str, config: Optional[Dict] = None) -> Dict:
    """
    Convenience function to parse a query.
    
    Usage:
        result = parse_query("פניות מאור גלילי")
        # Returns: {
        #   'intent': 'person',
        #   'entities': {'person_name': 'אור גלילי'},
        #   'target_fields': ['updatedby', 'createdby', ...]
        # }
    """
    parser = QueryParser(config)
    return parser.parse(query)

