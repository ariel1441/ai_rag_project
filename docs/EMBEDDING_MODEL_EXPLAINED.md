# Embedding Model Explained

## 🤖 What Model Are We Using?

**Model:** `sentence-transformers/all-MiniLM-L6-v2`

**What it is:**
- Pre-trained embedding model from HuggingFace
- Converts text → 384-dimensional vectors (numbers)
- Trained on billions of words (Wikipedia, books, web pages)
- Understands Hebrew, English, and many languages

**Size:** ~500MB (download)

---

## 📥 When & Where Was It Downloaded?

### Automatic Download (First Time You Run Script)

**When:** The first time you run any script that uses embeddings:
- `python scripts/core/generate_embeddings.py`
- `python scripts/core/search.py`
- Any test script

**Where it downloads:**
```
Windows: C:\Users\YourName\.cache\huggingface\hub\
Linux/Mac: ~/.cache/huggingface/hub/
```

**How it works:**
```python
from sentence_transformers import SentenceTransformer

# First time: Downloads automatically (~500MB, 5-10 minutes)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# After that: Loads from cache (instant, no download)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
```

**What happens:**
1. First run: Downloads model files from HuggingFace
2. Saves to cache directory
3. Next runs: Loads from cache (no download needed)

**You don't need to download it manually** - it happens automatically!

---

## 🔧 Do We Modify It for This Project?

### Short Answer: **NO, we don't modify it.**

### Why Not?

**The model is pre-trained:**
- Already trained on billions of words
- Already understands language (Hebrew, English, etc.)
- Already knows how to convert text → numbers
- **We just use it as-is**

**What we DO customize (not the model itself):**
1. **Field weighting** - We decide which fields to include and how many times
2. **Text combination** - We combine fields in a specific way
3. **Chunking** - We split text into chunks
4. **Search strategy** - We use hybrid search (keyword + semantic)

**The model itself stays the same** - we just feed it our data!

---

## 🎯 How It Works

### What the Model Does:

```
Input: "Project: אלינור | Updated By: אריאל בן עקיבא"
    ↓
[Model processes text]
    ↓
Output: [0.12, -0.45, 0.89, 0.23, ...] (384 numbers)
```

**The model:**
- Reads the text
- Understands the meaning
- Converts to numbers that represent meaning
- Similar text → Similar numbers

**We don't change the model** - we just give it our text!

---

## 🔄 Could We Fine-Tune It? (Optional)

### Yes, but we don't need to!

**Fine-tuning would:**
- Train the model on YOUR specific data
- Make it better understand YOUR terminology
- Take 4-12 hours
- Cost: Electricity for GPU time

**Why we don't do it:**
- RAG (next step) solves the problem without fine-tuning
- Pre-trained model is already good enough
- Field weighting gives us customization
- Faster to deploy without fine-tuning

**When you MIGHT fine-tune:**
- If search results aren't good enough
- If you have very specific terminology
- If quality requirements are very high
- **But for most cases, RAG is enough!**

---

## 📊 Model Details

**Name:** `sentence-transformers/all-MiniLM-L6-v2`

**Specs:**
- **Dimensions:** 384 numbers per embedding
- **Languages:** Multilingual (Hebrew, English, etc.)
- **Size:** ~500MB
- **Speed:** Fast (optimized for speed)
- **Quality:** Good (balance of speed and accuracy)

**Alternatives (if you want different):**
- `all-mpnet-base-v2`: 768 dimensions (more accurate, slower)
- `all-MiniLM-L12-v2`: 384 dimensions (similar to current)

**We chose this one because:**
- Fast (important for many clients)
- Good quality
- Multilingual (Hebrew support)
- Standard choice

---

## ✅ Summary

1. **Model:** `sentence-transformers/all-MiniLM-L6-v2` (pre-trained)
2. **Download:** Automatic on first use, cached locally
3. **Location:** `~/.cache/huggingface/hub/` (or `C:\Users\...\.cache\huggingface\hub\` on Windows)
4. **Modification:** NO - we use it as-is
5. **Customization:** We customize the INPUT (field weighting, text combination), not the model
6. **Fine-tuning:** Optional, but not needed (RAG is enough)

**The model is a tool** - we use it to convert our text to numbers. We don't change the tool, we just use it with our data!


