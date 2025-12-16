"""
Text processing utilities for embedding generation.
"""
from typing import Dict, List


def combine_text_fields(request: Dict, include_all_fields: bool = False) -> str:
    """
    Combine relevant text fields from a request into a single string.
    
    This is the CURRENT version (8 fields only).
    For improved version with field weighting, see combine_text_fields_weighted().
    
    Args:
        request: Dictionary containing request data
        include_all_fields: If True, includes all fields (not yet implemented)
        
    Returns:
        str: Combined text with field labels
    """
    fields = []
    
    # Current fields (8 total)
    if request.get('projectname'):
        fields.append(f"Project: {request['projectname']}")
    if request.get('projectdesc'):
        fields.append(f"Description: {request['projectdesc']}")
    if request.get('areadesc'):
        fields.append(f"Area: {request['areadesc']}")
    if request.get('remarks'):
        fields.append(f"Remarks: {request['remarks']}")
    if request.get('requestjobshortdescription'):
        fields.append(f"Job: {request['requestjobshortdescription']}")
    if request.get('requeststatusid'):
        fields.append(f"Status ID: {request['requeststatusid']}")
    if request.get('requesttypeid'):
        fields.append(f"Type ID: {request['requesttypeid']}")
    
    return " | ".join(fields) if fields else ""


def combine_text_fields_weighted(request: Dict) -> str:
    """
    Combine text fields with weighting (FINAL VERSION - Based on user feedback).
    
    This version includes:
    - All relevant text fields (~44 fields)
    - Field weighting (critical fields repeated 2-3 times)
    - Booleans and coordinates for specific queries
    - Proper field formatting
    
    Args:
        request: Dictionary containing request data
        
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
    
    # ============================================================================
    # WEIGHT 3.0x (Repeat 3 times - HIGHEST PRIORITY)
    # Core descriptive text - what users search for most
    # Based on UI analysis: Fields used in filters/sort are highest priority
    # ============================================================================
    critical_fields = [
        ('projectname', 'Project'),  # UI: Sort (שם הפרויקט)
        ('updatedby', 'Updated By'),  # CRITICAL - 99.9% coverage, UI: Sort (גורם מטפל)
        ('requesttypeid', 'Type'),  # UI: Filter (סוג הפניה) + Sort (מקור וסוג פניה)
        ('requeststatusid', 'Status'),  # UI: Filter (סטטוס) + Sort (סטטוס) - MOVED UP
        ('responsibleemployeename', 'Responsible Employee'),  # UI: Filter (גורם מטפל) + Sort (גורם מטפל) - MOVED UP
        ('requeststatusdate', 'Status Date'),  # UI: Filter (תאריך עדכון) + Sort (עדכון אחרון, זמן נותר למענה) - MOVED UP
        ('requestsourcenun', 'Request Source'),  # UI: Filter (מקור הפנייה) + Sort (מקור וסוג פניה) - MOVED UP
        ('createdby', 'Created By'),  # UI: Sort (יוזם הפניה) - MOVED UP
        ('areadesc', 'Area'),  # UI: Filter (מרחב)
        ('projectdesc', 'Description'),
        ('remarks', 'Remarks'),
    ]
    
    for field_key, field_label in critical_fields:
        value = get_value(field_key)
        if value:
            # Repeat 3 times for maximum emphasis
            for _ in range(3):
                fields.append(f"{field_label}: {value}")
    
    # ============================================================================
    # WEIGHT 2.0x (Repeat 2 times - HIGH PRIORITY)
    # Important identifiers and names
    # ============================================================================
    important_fields = [
        ('createddate', 'Created Date'),  # UI: Sort (תאריך פתיחה) - ADDED
        ('updatedate', 'Updated Date'),  # UI: Sort (עדכון אחרון - alternative) - ADDED
        ('requesttypereasonid', 'Type Reason'),
        ('contactfirstname', 'Contact First Name'),  # User said important
        ('contactlastname', 'Contact Last Name'),  # User said important
        ('contactemail', 'Contact Email'),  # User said important
        ('yazam_contactname', 'Yazam Contact'),  # User said important
        ('yazam_contactemail', 'Yazam Contact Email'),  # User said important
        ('yazam_companyname', 'Yazam Company'),
    ]
    
    for field_key, field_label in important_fields:
        value = get_value(field_key)
        if value:
            # Repeat 2 times for emphasis
            for _ in range(2):
                fields.append(f"{field_label}: {value}")
    
    # ============================================================================
    # WEIGHT 1.0x (Include once - MODERATE PRIORITY)
    # Supporting information
    # ============================================================================
    supporting_fields = [
        ('responsibleorgentityname', 'Responsible Organization'),
        ('responsibleemployeerolename', 'Responsible Role'),
        ('penetrategrounddesc', 'Penetrate Ground Description'),  # User said: when not empty, important
        ('requestjobshortdescription', 'Job Description'),  # User said: when not empty, important
        ('externalrequeststatusdesc', 'External Status'),
        ('penetrategroundtypeid', 'Penetrate Ground Type'),
        ('contactphone', 'Contact Phone'),
        ('yazam_contactphone', 'Yazam Contact Phone'),
        ('requestcontacttz', 'Contact TZ'),
        ('plannum', 'Plan Number'),
        # Note: requestsourcenun moved to 3.0x (critical_fields)
        # Note: requeststatusdate moved to 3.0x (critical_fields)
    ]
    
    for field_key, field_label in supporting_fields:
        value = get_value(field_key)
        if value:
            fields.append(f"{field_label}: {value}")
    
    # ============================================================================
    # WEIGHT 0.5x (Include once - LOW PRIORITY, for SPECIFIC queries)
    # Booleans and flags - important for specific queries, not general
    # ============================================================================
    boolean_fields = [
        ('ispenetrateground', 'Is Penetrate Ground'),  # User said: important to know if true/false
        ('isactive', 'Is Active'),  # User said: kinda important to know if true/false
        ('isconvert', 'Is Convert'),
        ('ismanual', 'Is Manual'),
        ('ismekorotlayer', 'Is Mekorot Layer'),
        ('isareafilevalid', 'Is Area File Valid'),
        ('ismekorottama1layer', 'Is Mekorot Tama1 Layer'),
        ('isimportentproject', 'Is Important Project'),
        ('isnewdocuments', 'Is New Documents'),
    ]
    
    for field_key, field_label in boolean_fields:
        value = get_value(field_key)
        if value is not None:
            # Convert boolean to text
            if isinstance(value, bool):
                bool_text = "true" if value else "false"
            elif str(value).lower() in ('true', '1', 'yes', 't', 'y'):
                bool_text = "true"
            elif str(value).lower() in ('false', '0', 'no', 'f', 'n', ''):
                bool_text = "false"
            else:
                bool_text = str(value)
            fields.append(f"{field_label}: {bool_text}")
    
    # ============================================================================
    # WEIGHT 0.5x (Include once - For SPATIAL queries)
    # Coordinates - for "close to each other" queries
    # ============================================================================
    # Format coordinates as text for semantic search
    area_center_x = get_value('areacenterx')
    area_center_y = get_value('areacentery')
    if area_center_x and area_center_y:
        fields.append(f"Area Center: {area_center_x}, {area_center_y}")
    
    extent_min_x = get_value('extentminx')
    extent_min_y = get_value('extentminy')
    extent_max_x = get_value('extentmaxx')
    extent_max_y = get_value('extentmaxy')
    if extent_min_x and extent_min_y and extent_max_x and extent_max_y:
        fields.append(f"Area Extent: {extent_min_x}, {extent_min_y}, {extent_max_x}, {extent_max_y}")
    
    area_in_square = get_value('areainsquare')
    if area_in_square:
        fields.append(f"Area Size: {area_in_square}")
    
    return " | ".join(fields) if fields else ""


def chunk_text(text: str, max_chunk_size: int = 512, overlap: int = 50) -> List[str]:
    """
    Split text into chunks with overlap.
    
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

