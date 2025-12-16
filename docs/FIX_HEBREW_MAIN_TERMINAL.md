# Fix Hebrew Display in Main Terminal

## The Problem

Hebrew displays correctly:
- ✅ In chat/output when I run scripts
- ❌ In your main terminal window

## Why This Happens

**When I run scripts**:
- Python automatically sets encoding
- Scripts include encoding fixes
- Output is redirected/processed

**Your terminal**:
- Uses default Windows encoding
- Doesn't automatically set UTF-8
- Needs manual configuration

## Solutions (Try in Order)

### Solution 1: Run Fix Script Before Python (Easiest)

**PowerShell**:
```powershell
.\scripts\fix_terminal_hebrew.ps1
python scripts\search.py
```

**CMD**:
```cmd
scripts\fix_terminal_hebrew.bat
python scripts\search.py
```

### Solution 2: Set Encoding Manually Before Each Script

**PowerShell**:
```powershell
chcp 65001
python scripts\search.py
```

**CMD**:
```cmd
chcp 65001
python scripts\search.py
```

### Solution 3: Create Alias/Function

**PowerShell Profile** (permanent):
```powershell
# Edit profile
notepad $PROFILE

# Add this:
function RunPython {
    chcp 65001 | Out-Null
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    python $args
}

# Then use:
RunPython scripts\search.py
```

### Solution 4: Use Windows Terminal (Best)

1. Install Windows Terminal from Microsoft Store
2. In Cursor: Settings → `terminal.integrated.defaultProfile.windows`
3. Set to: `Windows Terminal`
4. Restart terminal

**Why**: Windows Terminal has native Hebrew/RTL support

### Solution 5: Set Cursor Terminal Encoding

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

## Quick Test

After applying fix, run:
```bash
python -c "print('אלינור בדיקה')"
```

If Hebrew displays correctly, the fix worked!

## Why Scripts Work But Terminal Doesn't

**Scripts include**:
```python
os.system('chcp 65001 >nul 2>&1')
sys.stdout.reconfigure(encoding='utf-8')
```

**Your terminal**:
- Doesn't run these commands automatically
- Needs manual encoding setup
- Or needs to be set in terminal settings

## Recommended Approach

1. **Quick fix**: Run `chcp 65001` before each script
2. **Better**: Use Windows Terminal
3. **Best**: Set in Cursor settings + use Windows Terminal

## Troubleshooting

If `chcp 65001` doesn't work:
1. Check if you're in PowerShell or CMD
2. Try running as Administrator
3. Use Windows Terminal instead
4. Check Cursor terminal settings

