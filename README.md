# AI Requests System - RAG + Fine-Tuning POC

A complete Proof of Concept for building a custom AI system that answers questions about company requests using Retrieval-Augmented Generation (RAG) and fine-tuned language models.

## 🎯 Project Goal

Build an AI system that:
- Understands your company's "Requests" database
- Answers questions about requests (summaries, patterns, specific queries)
- Finds similar requests
- Can be fine-tuned on your specific data

## 📁 Project Structure

```
train_ai_tamar_request/
├── data/
│   ├── raw/              # Exported CSV/JSON from SQL Server
│   └── processed/         # Processed training data
├── scripts/               # All Python processing scripts
├── api/                   # FastAPI application
├── models/                # Trained models and adapters
│   ├── embeddings/        # Cached embedding models
│   └── lora_adapters/     # Fine-tuned LoRA adapters
├── config/                # Configuration files
├── sql/                   # SQL scripts
├── docs/                  # Documentation
└── notebooks/             # Jupyter notebooks for exploration
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### 2. Set Up PostgreSQL with pgvector

- Install PostgreSQL locally
- Install pgvector extension
- Create database: `ai_requests_db`
- Enable pgvector: `CREATE EXTENSION vector;`

### 3. Export Data from SQL Server

Use `scripts/export_requests.py` to export your Requests table to CSV.

### 4. Import to PostgreSQL

Import the CSV into the `requests` table in PostgreSQL.

### 5. Generate Embeddings

```bash
python scripts/generate_embeddings_from_db.py
```

### 6. Test Search

```bash
python scripts/search.py
```

## 📚 Current Status

✅ **Completed:**
- Data export from SQL Server
- PostgreSQL + pgvector setup
- Embedding generation pipeline
- Semantic similarity search
- Hybrid search (keyword + semantic)

🔄 **In Progress:**
- RAG pipeline (next step)
- Field weighting for embeddings

📋 **Planned:**
- Fine-tuning with LoRA/PEFT
- FastAPI endpoints
- Model evaluation

## 🔧 Configuration

Create a `.env` file in the project root:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DATABASE=ai_requests_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

## 📖 Documentation

See `full_guide.md` for the complete technical guide.

See `docs/` folder for specific topics:
- `UNDERSTANDING_EMBEDDINGS_AND_RAG.md` - Core concepts
- `FIX_HEBREW_MAIN_TERMINAL.md` - Hebrew display fixes
- `LOGIC_VERIFICATION_REPORT.md` - System verification

## 🛠️ Development

### Running Scripts

All scripts are in `scripts/`:
- `generate_embeddings_from_db.py` - Generate embeddings for all requests
- `search.py` - Interactive semantic search
- `verify_complete_logic.py` - Verify end-to-end logic

### Testing

```bash
python scripts/test_similarity_search.py
```

## 📝 Notes

- All data is stored in PostgreSQL (isolated from production)
- Embeddings are pre-computed and stored in `request_embeddings` table
- Hebrew text is handled correctly (RTL display fix applied)
- Search uses hybrid approach (keyword filtering + semantic ranking)

## 🔒 Security

- Never commit `.env` files
- Data is isolated in separate PostgreSQL instance
- PII sanitization recommended before export

## 📞 Support

For questions or issues, refer to:
1. `full_guide.md` - Complete technical documentation
2. `docs/` folder - Specific topic guides
3. Script comments - Inline documentation

