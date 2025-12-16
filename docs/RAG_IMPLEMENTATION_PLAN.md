# RAG Implementation Plan

## ✅ What We've Completed

1. **Embeddings** ✅
   - Regenerated with improved field weighting (8,195 requests, 36,031 chunks)
   - All relevant fields included

2. **Query Parser** ✅
   - Understands intent (person, project, type, etc.)
   - Extracts entities
   - Sets target fields

3. **Improved Search** ✅
   - Field-specific search
   - Boosting for exact matches
   - Type/status filtering
   - All tests passing

---

## 🚀 Next: Build RAG Pipeline

### What RAG Will Add

**Current:** Returns list of requests
**RAG:** Returns natural language answers

**Examples:**
- Query: "כמה פניות יש מאור גלילי?"
  - Current: List of requests
  - RAG: "יש 15 פניות שבהן updatedby = 'אור גלילי'"

- Query: "תביא לי סיכום של כל הפניות מסוג 4"
  - Current: List of requests
  - RAG: "יש 234 פניות מסוג 4. מתוכן: 120 פעילות, 80 ממתינות, 34 סגורות..."

---

## 📋 RAG Implementation Steps

### Step 1: Choose & Download LLM (1-2 hours)

**Recommended: Mistral-7B-Instruct**
- ✅ Open source (Apache 2.0)
- ✅ Good Hebrew support
- ✅ 7B parameters (manageable size ~4GB)
- ✅ Works on CPU (slower) or GPU (faster)

**Alternative: Llama 3 8B**
- ✅ Good performance
- ✅ Better Hebrew than older models
- ⚠️ Larger (~5GB)

**Download:**
```bash
# Using Hugging Face transformers
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained("mistralai/Mistral-7B-Instruct-v0.2")
```

---

### Step 2: Create RAG Script (2-3 hours)

**Components:**

1. **Retrieval** (use our improved search):
   ```python
   def retrieve_relevant_requests(query, top_k=20):
       # Use our current search.py logic
       results = semantic_search(query, top_k)
       return results
   ```

2. **Augmentation** (combine into context):
   ```python
   def create_context(retrieved_requests):
       context = ""
       for req in retrieved_requests:
           context += f"Request {req['id']}: {req['projectname']}...\n"
       return context
   ```

3. **Generation** (LLM answers):
   ```python
   def generate_answer(context, question):
       prompt = f"""Based on these requests:
{context}

Question: {question}
Answer:"""
       answer = llm.generate(prompt)
       return answer
   ```

---

### Step 3: Test RAG (1-2 hours)

**Test Queries:**
- "כמה פניות יש מאור גלילי?"
- "תביא לי סיכום של כל הפניות מסוג 4"
- "מה הפרויקטים הכי פעילים?"
- "איזה פניות יש מיניב ליבוביץ?"

**Verify:**
- Answers are correct
- Hebrew is correct
- Handles different question types

---

### Step 4: Optimize (1-2 hours)

**Improvements:**
- Better prompt templates
- Handle edge cases (no results, etc.)
- Improve context formatting
- Add error handling

---

## ⏱️ Timeline

**Total: 5-9 hours (1-1.5 days)**

- Step 1: Download LLM (1-2 hours)
- Step 2: Create RAG script (2-3 hours)
- Step 3: Test (1-2 hours)
- Step 4: Optimize (1-2 hours)

---

## 🎯 What We'll Build

**File:** `scripts/core/rag_query.py`

**Features:**
- Uses improved search for retrieval
- Formats context from retrieved requests
- Generates natural language answers
- Handles Hebrew queries
- Supports: find, count, summarize, similar

---

## ✅ Ready to Start?

I can:
1. Create the RAG script structure
2. Set up LLM loading (Mistral-7B)
3. Integrate with our improved search
4. Test with Hebrew queries

Should I start building the RAG pipeline now?

