# Fix Hebrew Display in Terminal

## The Problem

Hebrew displays correctly in:
- ✅ Chat/Output here (when I run scripts)
- ❌ Your main terminal window

## Why This Happens

**Different Encoding Contexts**:
1. **When I run scripts**: Python sets encoding automatically (`chcp 65001`)
2. **Your terminal**: Uses default Windows encoding (might be different)

## Solutions

### Solution 1: Run Encoding Fix Before Scripts (Easiest)

Add this to the start of every script:
```python
import os
os.system('chcp 65001 >nul 2>&1')
```

Or create a batch file:
```batch
@echo off
chcp 65001
python scripts\search_interactive.py
```

### Solution 2: Set Terminal Default Encoding

**In Cursor Settings**:
1. Open Settings (Ctrl+,)
2. Search: `terminal.integrated.encoding`
3. Set to: `utf8`
4. Restart terminal

**Or in settings.json**:
```json
{
    "terminal.integrated.encoding": "utf8"
}
```

### Solution 3: Use Windows Terminal (Best)

1. Install Windows Terminal from Microsoft Store
2. In Cursor: Settings → `terminal.integrated.defaultProfile.windows`
3. Set to: `Windows Terminal`
4. Restart terminal

**Why**: Windows Terminal has better Hebrew/RTL support

### Solution 4: PowerShell Profile (Permanent)

Edit PowerShell profile:
```powershell
notepad $PROFILE
```

Add:
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

Save and restart PowerShell.

## Quick Test

Run this to test:
```bash
python scripts/test_hebrew_display_fix.py
```

If Hebrew displays correctly, the fix worked!

## Why It Works in Chat But Not Terminal

**When I run scripts**:
- Python automatically sets `chcp 65001`
- Reconfigures stdout to UTF-8
- Sets environment variables

**Your terminal**:
- Uses default encoding (might be Windows-1255 or other)
- Doesn't automatically set UTF-8
- Needs manual configuration

## Recommended Solution

**Use Solution 3 (Windows Terminal)** - Best long-term solution!

Or add encoding fix to all scripts (Solution 1) - Quick fix!

