# Frontend - Simple Demo Interface

## Quick Start

### 1. Start API Server

```powershell
# From project root
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000
```

### 2. Open Frontend

**Option A: Direct file**
- Open `api/frontend/index.html` in your browser
- Note: Some browsers may block local file access to APIs
- If blocked, use Option B

**Option B: Simple HTTP server**
```powershell
# From api/frontend directory
cd api/frontend
python -m http.server 8080
# Then open: http://localhost:8080
```

## Features

- ✅ Search queries (Hebrew/English)
- ✅ Three modes:
  - Search only (fast, no LLM)
  - RAG retrieval only (fast, no LLM)
  - RAG with full answer (slower first time)
- ✅ Results display with expandable details
- ✅ Answer display (for RAG with LLM)
- ✅ Hebrew RTL support

## How to Use

1. Enter a query in Hebrew or English
2. Choose search type (radio buttons)
3. Click "חיפוש" (Search)
4. View results
5. Click on a result card to expand details

## Example Queries

- `פניות מאור גלילי` (requests from person)
- `כמה פניות יש מיניב ליבוביץ?` (count requests)
- `בקשות מסוג 4` (requests of type 4)
- `פרויקט אלינור` (project queries)

## Notes

- This is a simple demo interface
- Can be upgraded to React/Vue.js later
- Focus on functionality first, polish later
- Get feedback, then improve

