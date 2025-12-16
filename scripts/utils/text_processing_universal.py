"""
Universal text processing for embedding generation.

This is a GENERIC version that works with any table structure.
It uses configuration to determine which fields to include and their weights.

DO NOT modify scripts/utils/text_processing.py (project-specific).
"""
from typing import Dict, List


def combine_text_fields_universal(request: Dict, config: Dict) -> str:
    """
    Combine text fields from a request using configuration.
    
    This is the UNIVERSAL version that works with any table structure.
    Uses config to determine:
    - Which fields to include
    - Field weights (3.0x, 2.0x, 1.0x)
    - Field labels
    
    Args:
        request: Dictionary containing request data (any table structure)
        config: Configuration dict with field weights and labels
        
    Returns:
        str: Combined text with field labels and weighting
    """
    fields = []
    
    # Helper function to safely get value
    def get_value(key):
        value = request.get(key) or request.get(key.lower())
        if value is None:
            return None
        # Convert to string and strip
        value_str = str(value).strip()
        # Skip empty, NULL, or None strings
        if not value_str or value_str.upper() in ('NULL', 'NONE', ''):
            return None
        return value_str
    
    # Get field weights from config
    weights = config.get('fields', {}).get('weights', {})
    labels = config.get('fields', {}).get('labels', {})
    exclude = config.get('fields', {}).get('exclude', [])
    
    # Get all fields from request
    all_fields = list(request.keys())
    
    # Process fields by weight (highest first)
    for weight_level in ['3.0x', '2.0x', '1.0x']:
        weight_fields = weights.get(weight_level, [])
        repeat_count = {'3.0x': 3, '2.0x': 2, '1.0x': 1}.get(weight_level, 1)
        
        for field_key in weight_fields:
            # Skip if excluded
            if field_key in exclude:
                continue
            
            value = get_value(field_key)
            if value:
                # Get label (or use field name)
                label = labels.get(field_key, field_key.replace('_', ' ').title())
                
                # Repeat based on weight
                for _ in range(repeat_count):
                    fields.append(f"{label}: {value}")
    
    # Handle fields not in weight config (include once at 1.0x)
    # But only if include_all is True
    if config.get('fields', {}).get('include_all', False):
        for field_key in all_fields:
            # Skip if already processed or excluded
            if field_key in exclude:
                continue
            
            # Check if already in weights
            already_processed = False
            for weight_level in ['3.0x', '2.0x', '1.0x']:
                if field_key in weights.get(weight_level, []):
                    already_processed = True
                    break
            
            if not already_processed:
                value = get_value(field_key)
                if value:
                    # Only include text-like fields
                    field_lower = field_key.lower()
                    if any(word in field_lower for word in ['name', 'desc', 'text', 'content', 'remark', 'note', 'comment', 'message', 'title']):
                        label = labels.get(field_key, field_key.replace('_', ' ').title())
                        fields.append(f"{label}: {value}")
    
    return " | ".join(fields) if fields else ""


def chunk_text(text: str, max_chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Split text into chunks with overlap.
    
    This is the same as the project-specific version (generic logic).
    
    Args:
        text: Text to chunk
        max_chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List[str]: List of text chunks
    """
    if not text or len(text.strip()) == 0:
        return [""]
    
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    start = 0
    max_chunks = 100  # Safety limit to prevent memory issues
    iterations = 0
    max_iterations = len(text) // (max_chunk_size - overlap) + 10  # Safety limit
    
    while start < len(text) and iterations < max_iterations and len(chunks) < max_chunks:
        iterations += 1
        end = start + max_chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for period or pipe separator
            for sep in ['. ', ' | ']:
                last_sep = text.rfind(sep, start, end)
                if last_sep != -1:
                    end = last_sep + len(sep)
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Calculate next start position
        next_start = end - overlap
        if next_start <= start:  # Safety check to prevent infinite loop
            next_start = start + max_chunk_size - overlap
        
        start = next_start
        
        if start >= len(text):
            break
    
    # If we hit the limit, just return the whole text as one chunk
    if len(chunks) >= max_chunks:
        return [text]
    
    return chunks if chunks else [text]

