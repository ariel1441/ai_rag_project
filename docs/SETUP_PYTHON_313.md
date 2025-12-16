# Python 3.13 Setup Guide - Enable 4-bit Quantization

## Step 1: Download Python 3.13

1. Go to: https://www.python.org/downloads/release/python-3131/
2. Download: **Windows installer (64-bit)** - `python-3.13.1-amd64.exe`
3. Run the installer
4. **IMPORTANT:** Check "Add Python 3.13 to PATH" during installation
5. Click "Install Now"

## Step 2: Verify Installation

Open a **NEW** PowerShell window and run:
```powershell
py -3.13 --version
```

You should see: `Python 3.13.1`

## Step 3: Create Virtual Environment

In your project directory, run:
```powershell
cd D:\ai_learning\train_ai_tamar_request
py -3.13 -m venv venv313
```

## Step 4: Activate Virtual Environment

```powershell
.\venv313\Scripts\Activate.ps1
```

If you get an execution policy error, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again.

## Step 5: Install Packages

```powershell
pip install -r requirements.txt
```

This will take a few minutes. You should see `bitsandbytes` install successfully!

## Step 6: Test Model Loading

```powershell
python scripts/tests/test_model_loading_only.py
```

You should see:
- ✅ "Attempting 4-bit quantization (~4GB RAM)"
- ✅ "Loaded with 4-bit quantization (~4GB RAM)"
- ✅ Model loads successfully (no crash at 67%)

## Step 7: Run Full RAG Tests

```powershell
python scripts/tests/test_rag_comprehensive_final.py
```

---

## Quick Setup Script

I've created `setup_python313.ps1` - you can run it after installing Python 3.13!

