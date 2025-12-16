"""
Hebrew text utilities.
"""
import os
import sys
import re


def fix_hebrew_rtl(text):
    """
    Fix Hebrew RTL display for LTR terminals.
    Reverses Hebrew text segments so they display correctly.
    
    IMPORTANT: Data in database is CORRECT - this is display only!
    
    Args:
        text: Text string that may contain Hebrew
        
    Returns:
        str: Text with Hebrew segments reversed for correct display
    """
    if not text:
        return text
    
    # Hebrew Unicode range: \u0590-\u05FF
    # Split text into Hebrew and non-Hebrew segments
    pattern = r'([\u0590-\u05FF]+|[^\u0590-\u05FF]+)'
    parts = re.findall(pattern, str(text))
    
    result = []
    for part in parts:
        # If Hebrew text, reverse it for display
        if re.match(r'[\u0590-\u05FF]+', part):
            result.append(part[::-1])
        else:
            result.append(part)
    
    return ''.join(result)


def setup_hebrew_encoding():
    """
    Setup terminal encoding for Hebrew text display on Windows.
    Should be called at the start of scripts that display Hebrew text.
    """
    if sys.platform == 'win32':
        try:
            os.system('chcp 65001 >nul 2>&1')
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            os.environ['PYTHONIOENCODING'] = 'utf-8'
        except:
            pass

