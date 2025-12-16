# Terminal Shortcuts & Tips

## Copy/Paste in PowerShell/CMD

### Copy Text from Terminal
- **PowerShell**: `Ctrl+Shift+C` (or right-click → Copy)
- **CMD**: Right-click → Mark → Select text → Enter (copies)
- **Windows Terminal**: `Ctrl+Shift+C` or right-click

### Paste into Terminal
- **PowerShell**: `Ctrl+Shift+V` (or right-click → Paste)
- **CMD**: Right-click → Paste
- **Windows Terminal**: `Ctrl+Shift+V` or right-click

### ⚠️ Important
- **`Ctrl+C`** = Cancel/Interrupt running command (NOT copy!)
- **`Ctrl+V`** = May not work in some terminals
- Always use **`Ctrl+Shift+C`** and **`Ctrl+Shift+V`** for copy/paste

---

## Python Commands on Windows

### Installing Packages
```bash
# ❌ This might not work:
pip install package_name

# ✅ Use this instead:
python -m pip install package_name

# Or if you have multiple Python versions:
py -m pip install package_name
```

### Running Scripts
```bash
# ✅ Correct way:
python scripts/script_name.py

# Or:
py scripts/script_name.py
```

### Checking Python/Pip
```bash
python --version
python -m pip --version
```

---

## Useful PowerShell Shortcuts

- **`Ctrl+C`**: Cancel/interrupt current command
- **`Ctrl+L`**: Clear screen (or `cls`)
- **`Ctrl+Shift+C`**: Copy selected text
- **`Ctrl+Shift+V`**: Paste text
- **`Tab`**: Auto-complete file/folder names
- **`Up Arrow`**: Previous command
- **`Ctrl+R`**: Search command history

---

## Quick Tips

1. **Select Text**: Click and drag to select, then use `Ctrl+Shift+C`
2. **Multi-line Commands**: Use backtick `` ` `` at end of line to continue
3. **Clear Terminal**: Type `cls` or press `Ctrl+L`
4. **Stop Script**: Press `Ctrl+C` (this is why copy doesn't work with Ctrl+C!)

---

## If Copy Still Doesn't Work

1. **Right-click** on terminal → Select "Mark"
2. **Drag** to select text
3. **Press Enter** (copies to clipboard)
4. Or use **Windows Terminal** (better support)

