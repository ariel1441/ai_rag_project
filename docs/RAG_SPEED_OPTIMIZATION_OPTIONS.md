# RAG Speed Optimization Options

**Problem:** RAG generation is very slow (10-30+ minutes per query on CPU)

**Root Cause:** CPU inference is inherently slow for LLMs (7B parameters)

---

## Current Performance

### CPU (Your Current Setup):
- **Model loading:** 2-5 minutes (one-time, first query)
- **Generation:** 10-30+ minutes per query
- **Total per query:** 12-35 minutes

### GPU (If Available):
- **Model loading:** 30-60 seconds (one-time)
- **Generation:** 5-15 seconds per query
- **Total per query:** 6-16 seconds (after first load)

**Speed difference:** 100-1000x faster with GPU!

---

## Optimization Options

### Option 1: Use GPU (Best Performance) ⚡

**Requirements:**
- NVIDIA GPU with CUDA support
- 8GB+ VRAM (for float16 model)
- CUDA Toolkit installed
- PyTorch with CUDA

**Your Current GPU:**
- Intel HD Graphics 4600
- ❌ **Does NOT support CUDA**
- ❌ **Cannot use for LLM inference**

**If You Get NVIDIA GPU:**
- ✅ **100-1000x faster**
- ✅ **Same accuracy**
- ✅ **No code changes needed** (already detects GPU automatically)

**Cost:** New GPU purchase ($200-1000+)

---

### Option 2: Use API-Based LLM (Fast, But Costs Money) 💰

**Services:**
- OpenAI GPT-4 / GPT-3.5
- Anthropic Claude
- Google Gemini
- Mistral AI API

**Performance:**
- **Generation:** 2-10 seconds per query
- **No model loading** (handled by API)
- **Total per query:** 2-10 seconds

**Cost:**
- GPT-3.5: ~$0.001-0.01 per query
- GPT-4: ~$0.01-0.10 per query
- Claude: ~$0.01-0.05 per query

**Implementation:**
- Replace local model with API calls
- Fast, but ongoing costs
- Requires internet connection

**Code Changes:**
```python
# Instead of local model:
# self.model.generate(...)

# Use API:
import openai
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": prompt}]
)
```

---

### Option 3: Continue with CPU (Free, But Slow) 🐌

**Current Status:**
- ✅ Already optimized for CPU
- ✅ Greedy decoding (faster)
- ✅ Reduced tokens (200 instead of 500)
- ✅ Memory efficient loading

**Limitations:**
- ⚠️ Still very slow (10-30+ minutes)
- ⚠️ Not practical for interactive use
- ✅ Free (no costs)

**Best For:**
- Batch processing (run overnight)
- One-time queries
- Testing/development

---

### Option 4: Smaller Model (Faster, But Less Accurate) 📉

**Options:**
- Mistral-7B-Instruct (current) - 7B parameters
- Smaller models: 1B-3B parameters
- Quantized models: 4-bit, 8-bit

**Performance:**
- **1B model:** 2-5 minutes per query (CPU)
- **3B model:** 5-10 minutes per query (CPU)
- **4-bit quantized:** 3-8 minutes per query (CPU)

**Trade-offs:**
- ⚠️ Less accurate (70-85% vs 85-95%)
- ⚠️ Less capable
- ✅ Faster on CPU

**Not Recommended:** Quality loss not worth the speed gain

---

### Option 5: Hybrid Approach (Best of Both Worlds) 🎯

**Strategy:**
- Use **retrieval-only** for most queries (fast, no LLM)
- Use **full RAG** only when needed (slow, but accurate)

**Implementation:**
- Default to `use_llm=False` (retrieval only)
- User can opt-in to `use_llm=True` for important queries
- Fast for most cases, accurate when needed

**Performance:**
- **Retrieval-only:** 1-3 seconds
- **Full RAG:** 10-30+ minutes (when needed)

**Best For:**
- Most users just want to find requests (fast)
- Some users want summaries (can wait)

---

## Recommended Approach

### Short Term (Now):
1. ✅ **Continue with CPU** (already optimized)
2. ✅ **Use retrieval-only by default** (fast)
3. ✅ **Full RAG as optional** (when user needs it)

### Medium Term (If Budget Allows):
1. ✅ **Try API-based LLM** (OpenAI GPT-3.5)
   - Fast (2-10 seconds)
   - Low cost (~$0.001-0.01 per query)
   - Good quality
2. ✅ **Test with real queries**
3. ✅ **Compare quality vs cost**

### Long Term (If Performance Critical):
1. ✅ **Get NVIDIA GPU** (if budget allows)
   - Best performance
   - No ongoing costs
   - 100-1000x faster

---

## Implementation: API-Based LLM

If you want to try API-based LLM, here's how:

### Step 1: Install API Library
```bash
pip install openai
# or
pip install anthropic
```

### Step 2: Add API Key to .env
```
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
```

### Step 3: Create API Wrapper
```python
# scripts/core/rag_query_api.py
import openai
import os

class RAGSystemAPI:
    """RAG system using OpenAI API instead of local model."""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        openai.api_key = self.api_key
        self.model = "gpt-3.5-turbo"  # or "gpt-4"
    
    def generate_answer(self, prompt: str) -> str:
        """Generate answer using OpenAI API."""
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "אתה עוזר מועיל שעונה על שאלות בעברית."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
```

### Step 4: Use in RAGService
```python
# In api/services.py, add option:
def query(self, query: str, top_k: int = 20, use_llm: bool = True, use_api: bool = False):
    if use_api:
        # Use API-based LLM (fast)
        rag_api = RAGSystemAPI()
        # ... generate with API
    else:
        # Use local model (slow but free)
        # ... existing code
```

---

## Cost Comparison

### Local CPU (Current):
- **Cost:** $0 (free)
- **Speed:** 10-30+ minutes
- **Quality:** 85-95%

### API (GPT-3.5):
- **Cost:** ~$0.001-0.01 per query
- **Speed:** 2-10 seconds
- **Quality:** 90-95%

### API (GPT-4):
- **Cost:** ~$0.01-0.10 per query
- **Speed:** 5-15 seconds
- **Quality:** 95-98%

### GPU (If Available):
- **Cost:** $0 (after purchase)
- **Speed:** 5-15 seconds
- **Quality:** 85-95%

---

## Recommendation

**For Now:**
1. ✅ Keep current CPU setup (free, works)
2. ✅ Use retrieval-only for most queries (fast)
3. ✅ Full RAG only when needed (slow but accurate)

**If Speed Becomes Critical:**
1. ✅ Try API-based LLM (GPT-3.5)
   - Fast and affordable
   - Easy to implement
   - Good quality

**If Budget Allows:**
1. ✅ Get NVIDIA GPU
   - Best long-term solution
   - No ongoing costs
   - Fastest performance

---

## Summary

**Current:** CPU inference is slow (10-30+ min) but free

**Options:**
1. **GPU** - Fastest, but need to buy GPU
2. **API** - Fast, but costs money per query
3. **CPU** - Free, but very slow
4. **Hybrid** - Fast for most, slow when needed

**Best approach:** Use retrieval-only by default, full RAG when needed, consider API if speed becomes critical.

