# Fix Hebrew RTL (Right-to-Left) Display Issue

## The Problem

Hebrew text displays **backwards** in terminal:
- Should show: **אלינור**
- Actually shows: **רונילא** (reversed)

This is a **bidirectional text (RTL) rendering issue**, not an encoding issue.

## Understanding the Issue

### What's Happening

1. **Data is CORRECT** in database (stored as UTF-8)
2. **Terminal renders RTL text incorrectly** (Windows PowerShell/CMD limitation)
3. **Characters are correct**, but **order is reversed**

### Why This Happens

- **Hebrew is RTL** (right-to-left)
- **Windows terminals** don't handle RTL well by default
- **PowerShell/CMD** render Hebrew characters left-to-right
- **Windows Terminal** handles RTL better

## Solutions

### Solution 1: Use Windows Terminal (BEST - Recommended)

**Why**: Windows Terminal has native RTL support

**Steps**:
1. Install Windows Terminal from Microsoft Store
2. Open Cursor Settings (Ctrl+,)
3. Search: `terminal.integrated.defaultProfile.windows`
4. Set to: `Windows Terminal`
5. Restart Cursor

**Or in settings.json**:
```json
{
    "terminal.integrated.defaultProfile.windows": "Windows Terminal"
}
```

**Result**: Hebrew displays correctly (RTL) automatically!

### Solution 2: Use PowerShell with RTL Support

**Create PowerShell profile**:
```powershell
# Edit profile
notepad $PROFILE

# Add this:
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

# Enable bidirectional text
$Host.UI.RawUI.BufferSize = New-Object System.Management.Automation.Host.Size(120, 3000)
```

**Then restart PowerShell**

### Solution 3: Use Python Script to Reverse Display (Workaround)

**Create wrapper script** that reverses Hebrew text for display:

```python
# scripts/display_hebrew.py
import unicodedata
import re

def fix_hebrew_display(text):
    """Reverse Hebrew text segments for correct display in LTR terminals."""
    # Split by Hebrew and non-Hebrew
    pattern = r'([\u0590-\u05FF]+|[^\u0590-\u05FF]+)'
    parts = re.findall(pattern, text)
    
    result = []
    for part in parts:
        # If Hebrew, reverse it
        if re.match(r'[\u0590-\u05FF]+', part):
            result.append(part[::-1])
        else:
            result.append(part)
    
    return ''.join(result)
```

**Use in scripts**:
```python
from display_hebrew import fix_hebrew_display
print(fix_hebrew_display("אלינור"))  # Will display correctly
```

### Solution 4: Use pgAdmin for Viewing Results

**Why**: pgAdmin displays Hebrew correctly

**How**:
1. Run search script
2. Copy request IDs from results
3. Query in pgAdmin:
   ```sql
   SELECT requestid, projectname, text_chunk
   FROM request_embeddings
   WHERE requestid IN ('211000007', '211000008', ...);
   ```
4. View results in pgAdmin (Hebrew displays correctly)

### Solution 5: Export to File (Workaround)

**Modify scripts to write to file**:
```python
# In search script, add:
with open('results.txt', 'w', encoding='utf-8') as f:
    for result in results:
        f.write(f"{result}\n")

print("Results saved to results.txt")
print("Open in Notepad++ or VS Code to see Hebrew correctly")
```

Then open `results.txt` in Notepad++ or VS Code (they handle RTL correctly).

## Quick Test

**Test if it's display issue**:
```python
# Check actual data
text = "אלינור"
print(f"Stored: {text}")
print(f"Bytes: {text.encode('utf-8')}")
print(f"Reversed: {text[::-1]}")
```

If bytes are correct but display is reversed → **Display issue**
If bytes are reversed → **Data issue**

## Recommended Solution

**Use Windows Terminal** (Solution 1):
- ✅ Native RTL support
- ✅ Works automatically
- ✅ No code changes needed
- ✅ Best long-term solution

**If Windows Terminal not available**:
- Use Solution 4 (pgAdmin) for viewing
- Or Solution 5 (export to file)

## Why It Works in Chat But Not Terminal

**When I run scripts**:
- Output is processed/redirected
- May use different rendering
- Chat interface handles RTL better

**Your terminal**:
- Direct console output
- Windows PowerShell/CMD RTL limitation
- Needs Windows Terminal for proper RTL

## Summary

| Issue | Cause | Solution |
|-------|-------|----------|
| Hebrew backwards | RTL rendering | Windows Terminal |
| Encoding errors | Wrong code page | `chcp 65001` |
| Both | Multiple issues | Windows Terminal + UTF-8 |

**Best Fix**: Install Windows Terminal and set as default in Cursor.

