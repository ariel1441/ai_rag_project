# RAG System - Complete Guide

**Everything about RAG (Retrieval-Augmented Generation): LLM model, context formatting, answer generation, and system versions**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [What is RAG?](#what-is-rag)
3. [LLM Model](#llm-model)
4. [RAG Flow](#rag-flow)
5. [Context Formatting](#context-formatting)
6. [Answer Generation](#answer-generation)
7. [System Versions](#system-versions)
8. [Configuration](#configuration)

---

## Overview

**Goal:** Generate natural language answers from retrieved requests using LLM.

**What We Do:**
- Retrieve relevant requests using search
- Format requests into context for LLM
- Build query-specific prompts
- Generate natural language answers
- Extract and return answers

**Result:** System can answer questions like "כמה פניות יש מיניב ליבוביץ?" with natural Hebrew text

---

## What is RAG?

### RAG = Retrieval-Augmented Generation

**Two-Phase Process:**

1. **Retrieval Phase:**
   - Uses search system to find relevant requests
   - Same as Type 1 search (embedding model + vector search)
   - Returns top-k relevant requests

2. **Generation Phase:**
   - Formats retrieved requests into context
   - Sends context + query to LLM
   - LLM generates natural language answer

### Why RAG?

**Without RAG (Search Only):**
- Returns list of requests
- User must read and interpret
- No direct answers

**With RAG:**
- Returns natural language answer
- Answers questions directly
- Summarizes results
- More user-friendly

---

## LLM Model

### Model Details

**Name:** Mistral-7B-Instruct-v0.2

**Specs:**
- **Size:** ~4GB (4-bit) or ~7-8GB (float16)
- **Type:** Instruction-tuned (good for Q&A)
- **Languages:** Multilingual (Hebrew, English)
- **Location:** `models/llm/mistral-7b-instruct/`

### Model Loading

**First Time (Slow):**
- Loads model into RAM
- 2-5 minutes (float16) or 30-60 seconds (4-bit)
- Model stays in memory after loading

**Subsequent Queries (Fast):**
- Model already loaded
- 5-15 seconds per query
- No reload needed

**Lazy Loading:**
- Model loads only when first RAG query with `use_llm=true`
- Not loaded at server startup
- Saves RAM when not using RAG

### Quantization Options

**4-bit Quantization (~4GB RAM):**
- Best performance
- Requires bitsandbytes library
- May hang on Windows CPU (known issue)
- Use on servers/high-end PCs

**float16 (~7-8GB RAM):**
- Compatible everywhere
- Works on Windows CPU
- Slightly slower than 4-bit
- Use on limited systems

**Key Files:**
- `scripts/core/rag_query.py` - Compatible version (float16)
- `scripts/core/rag_query_high_end.py` - High-end version (4-bit)

---

## RAG Flow

### Complete Process

```
User Query: "כמה פניות יש מאור גלילי?"
  ↓
[Query Parser] → Intent: person, Entity: "אור גלילי", Type: count
  ↓
[Retrieval] → Uses search system (field-specific, boosting)
  ↓
[Context Formatting] → Formats 20 relevant requests
  ↓
[Prompt Building] → Query-type-specific prompt
  ↓
[LLM Generation] → Generates: "יש 15 פניות שבהן updatedby = 'אור גלילי'"
  ↓
[Answer Extraction] → Extracts clean answer
  ↓
[Return] → Natural language response + list of requests
```

### Query Types Supported

1. **Find Queries:**
   - "תביא לי פניות מאור גלילי"
   - Returns: List of requests + explanation

2. **Count Queries:**
   - "כמה פניות יש מאור גלילי?"
   - Returns: Number + breakdown

3. **Summarize Queries:**
   - "תביא לי סיכום של כל הפניות מסוג 4"
   - Returns: Summary with statistics

4. **Similar Queries:**
   - "תביא לי פניות דומות ל-211000001"
   - Returns: Similar requests + explanation

---

## Context Formatting

### Purpose

**Convert retrieved requests into text** that LLM can understand.

### How It Works

**For Person Queries:**
```
בקשה 211000001:
- פרויקט: בנית בנין C1
- עודכן על ידי: אור גלילי
- נוצר על ידי: אתר חיצוני תמר
- סוג: 4
- סטטוס: 10

בקשה 211000002:
- פרויקט: פרויקט בדיקה
- עודכן על ידי: אור גלילי
- ...
```

**For Count Queries:**
```
נמצאו 20 בקשות רלוונטיות:
1. בקשה 211000001: עודכן על ידי אור גלילי
2. בקשה 211000002: עודכן על ידי אור גלילי
...
```

**Key File:** `scripts/core/rag_query.py` - `format_context()` function

---

## Answer Generation

### Prompt Building

**Uses Mistral's chat template:**
```python
messages = [
    {"role": "user", "content": prompt}
]
formatted_prompt = tokenizer.apply_chat_template(messages, tokenize=False)
```

**Query-Type-Specific Prompts:**

**For Count Queries:**
```
תבסס על הבקשות הבאות:
[context]

שאלה: כמה פניות יש מאור גלילי?

ענה בעברית בצורה ברורה ומדויקת.
```

**For Find Queries:**
```
תבסס על הבקשות הבאות:
[context]

שאלה: תביא לי פניות מאור גלילי

ענה בעברית וציין את הבקשות הרלוונטיות.
```

### Generation Parameters

**Current Settings:**
- **Temperature:** 0.7 (balanced creativity/accuracy)
- **Max Length:** 500 tokens
- **Do Sample:** True (allows variation)

**How to change:**
```python
# In rag_query.py
outputs = model.generate(
    inputs,
    max_length=500,  # Change to 300 for shorter answers
    temperature=0.7,  # Change to 0.5 for more focused
    do_sample=True
)
```

### Answer Extraction

**Process:**
1. LLM generates text with special tokens
2. Extract answer between markers
3. Clean up special tokens
4. Return clean answer

**Key File:** `scripts/core/rag_query.py` - `generate_answer()` function

---

## System Versions

### Two Versions

**1. High-End Version (`rag_query_high_end.py`):**
- 4-bit quantization (~4GB RAM)
- GPU acceleration if available
- Best performance
- For servers/high-end PCs

**2. Compatible Version (`rag_query.py`):**
- float16 loading (~7-8GB RAM)
- CPU-only (more stable)
- Works on Windows CPU
- For limited systems

### When to Use Which

**Use High-End Version when:**
- ✅ You have 16GB+ RAM
- ✅ You have GPU (optional)
- ✅ You're on Linux/server
- ✅ You want best performance

**Use Compatible Version when:**
- ✅ You're on Windows CPU
- ✅ You have 8-12GB RAM
- ✅ 4-bit quantization fails
- ✅ You need maximum compatibility

**Key Files:**
- `scripts/core/rag_query.py` - Compatible version
- `scripts/core/rag_query_high_end.py` - High-end version
- `docs/RAG_SYSTEM_VERSIONS.md` - Detailed comparison

---

## Configuration

### Model Path

**Location:** `scripts/core/rag_query.py`

**Current:** `models/llm/mistral-7b-instruct/`

**How to change:**
```python
rag = RAGSystem(model_path="path/to/your/model")
```

### Retrieval Settings

**Top-K:**
- Default: 20 requests
- How to change: `rag.query(query, top_k=30)`

**Impact:**
- More requests = better context, slower generation
- Fewer requests = faster, may miss relevant info

### Generation Settings

**Max Length:**
- Default: 500 tokens
- How to change: Modify `max_length` in `generate_answer()`

**Temperature:**
- Default: 0.7
- How to change: Modify `temperature` in `generate_answer()`

**Impact:**
- Higher temperature = more creative, less focused
- Lower temperature = more focused, less creative

---

## Making RAG More/Less Focused

### More Focused:

1. **Decrease temperature:** `0.7 → 0.5`
2. **Decrease max_length:** `500 → 300`
3. **Set do_sample to False:** More deterministic

### More Creative:

1. **Increase temperature:** `0.7 → 0.9`
2. **Increase max_length:** `500 → 800`
3. **Keep do_sample True:** More variation

---

## Summary

**Complete RAG Process:**
1. Parse query (intent, entities)
2. Retrieve relevant requests (using search)
3. Format context (prepare for LLM)
4. Build prompt (query-type-specific)
5. Generate answer (using LLM)
6. Extract answer (clean up)
7. Return answer + requests

**Key Points:**
- RAG uses search for retrieval
- LLM generates natural language answers
- Two versions (high-end and compatible)
- Lazy loading saves RAM
- Query-type-specific prompts improve quality

**Key Files:**
- `scripts/core/rag_query.py` - Compatible RAG system
- `scripts/core/rag_query_high_end.py` - High-end RAG system
- `api/services.py` - RAGService (API integration)

---

**Last Updated:** Current Session  
**Status:** Complete, ready for testing

