# Percentage Accuracy - What Are They Based On?

## ⚠️ Important: These Are ESTIMATES, Not Tested Results

The percentages I mentioned (85-95%, 95-100%, etc.) are **educated estimates** based on:

1. **General LLM performance** (Mistral-7B capabilities)
2. **Task complexity** (simple vs. complex)
3. **Prompt quality** (how clear the instructions are)
4. **Industry standards** (typical RAG system performance)
5. **Code analysis** (what the prompts/instructions look like)

**They are NOT based on:**
- ❌ Actual testing of this system
- ❌ Real query results
- ❌ Measured accuracy
- ❌ User feedback

---

## How I Estimated Each Type

### 1. **`find` - 85-95%**

**Why this range:**
- **Task:** Summarize retrieved requests
- **Complexity:** Medium (needs to understand context, summarize)
- **LLM strength:** Good at summarization
- **Prompt quality:** Clear instructions ("אל תפרט כל פנייה")
- **Risk factors:** 
  - Might miss important details
  - Might be too generic
  - Depends on retrieval quality

**Based on:**
- Mistral-7B is good at summarization tasks
- Clear prompts help
- But summarization can miss nuances

---

### 2. **`count` - 95-100%**

**Why this range:**
- **Task:** Count items in context
- **Complexity:** Very simple (just count)
- **LLM strength:** Excellent at counting
- **Prompt quality:** Very clear ("ספור את הפניות")
- **Risk factors:** 
  - Minimal (counting is straightforward)
  - Might miscount if context is confusing

**Based on:**
- Counting is one of the simplest tasks for LLMs
- Mistral-7B should handle this very well
- Clear, simple instruction

---

### 3. **`count` + `projects` - 100%**

**Why this range:**
- **Task:** Group and count (NO LLM - direct code)
- **Complexity:** None (just Python code)
- **LLM strength:** N/A (no LLM used)
- **Code quality:** Direct calculation, no AI involved
- **Risk factors:** 
  - None (deterministic code)

**Based on:**
- This is NOT an estimate - it's deterministic code
- Python `dict` grouping and counting
- No AI, no randomness, 100% accurate

---

### 4. **`summarize` - 70-85%**

**Why this range:**
- **Task:** Detailed summary with statistics
- **Complexity:** High (needs to calculate stats, find patterns)
- **LLM strength:** Good but not perfect at statistics
- **Prompt quality:** Clear but complex requirements
- **Risk factors:**
  - Only 20 requests in context (might not represent full dataset)
  - Statistics might be inaccurate
  - Patterns might be missed
  - LLM might hallucinate statistics

**Based on:**
- Statistics require more context
- LLMs can make calculation errors
- Pattern detection is harder
- Limited context (20 requests) might not be enough

---

### 5. **`urgent` - 90-95%**

**Why this range:**
- **Task:** List urgent requests with deadlines
- **Complexity:** Medium (formatting + date calculations)
- **LLM strength:** Good at structured output
- **Prompt quality:** Clear format instructions
- **Risk factors:**
  - Date calculations might be wrong
  - Formatting might be inconsistent

**Based on:**
- Clear format instructions help
- Date calculations are straightforward
- But LLMs can make date math errors

---

### 6. **`similar` - 75-85%**

**Why this range:**
- **Task:** Explain why requests are similar
- **Complexity:** Medium-high (needs to identify commonalities)
- **LLM strength:** Moderate at explanation tasks
- **Prompt quality:** Clear but explanation is subjective
- **Risk factors:**
  - Explanations might be generic
  - Might miss subtle similarities
  - Might focus on wrong aspects

**Based on:**
- Explanation tasks are harder than summarization
- LLMs can be generic in explanations
- Similarity is somewhat subjective

---

### 7. **`answer_retrieval` - 60-75%**

**Why this range:**
- **Task:** Extract answer from similar request
- **Complexity:** High (needs to identify which field has the answer)
- **LLM strength:** Moderate (depends on data structure)
- **Prompt quality:** Clear but task is complex
- **Risk factors:**
  - Might not find the answer field
  - Answer might not exist in data
  - Might extract wrong information
  - Data structure might not support this

**Based on:**
- This is experimental
- Depends heavily on data structure
- LLMs struggle with field identification
- No clear "answer" field in your schema

---

## Factors That Affect Accuracy

### 1. **Retrieval Quality**
- If retrieval finds wrong requests → LLM gets wrong context → bad answer
- **Impact:** High (garbage in, garbage out)

### 2. **Prompt Clarity**
- Clear prompts → better answers
- Vague prompts → generic/wrong answers
- **Impact:** Medium-High

### 3. **Context Size**
- 20 requests might not be enough for statistics
- More context → better answers (usually)
- **Impact:** Medium

### 4. **Task Complexity**
- Simple tasks (count) → high accuracy
- Complex tasks (summarize) → lower accuracy
- **Impact:** High

### 5. **LLM Model Quality**
- Mistral-7B is good but not perfect
- Larger models would be better
- **Impact:** Medium

### 6. **Data Quality**
- Clean, structured data → better answers
- Messy data → worse answers
- **Impact:** Medium

---

## Industry Benchmarks (For Reference)

**Note:** These are general benchmarks, not specific to this system.

| Task Type | Typical RAG Accuracy | Notes |
|-----------|---------------------|-------|
| Simple QA | 80-90% | Direct questions |
| Summarization | 70-85% | Depends on context size |
| Counting | 90-100% | Very reliable |
| Complex Analysis | 60-80% | Requires more context |
| Explanation | 70-85% | Can be generic |

**Source:** General RAG system performance (various papers, industry reports)

---

## What Would Make These More Accurate?

### 1. **Actual Testing**
- Run 100 queries of each type
- Measure accuracy manually
- Calculate real percentages

### 2. **User Feedback**
- Collect feedback on answer quality
- Measure user satisfaction
- Track which types work best

### 3. **A/B Testing**
- Compare different prompts
- Measure which works better
- Iterate based on results

### 4. **Automated Evaluation**
- Create test set with expected answers
- Automatically compare LLM output
- Calculate precision/recall

---

## Realistic Expectations

### What Will Likely Work Well:
- ✅ **Count queries** - Simple, should be 90%+
- ✅ **Find queries** - Medium complexity, should be 80%+
- ✅ **Project counting** - Deterministic, 100%

### What Might Need Refinement:
- ⚠️ **Summarize** - Might need more context or better prompts
- ⚠️ **Similar** - Explanations might be too generic
- ⚠️ **Answer retrieval** - Experimental, might not work well

### What to Expect:
- **First attempts:** Might be 60-80% accurate
- **After refinement:** Should improve to 80-95%
- **Some types:** Might need significant work

---

## How to Validate These Estimates

### Quick Test (1 query per type):
1. Run one query of each type
2. Manually evaluate answer quality
3. Compare to estimate
4. Adjust expectations

### Full Test (10+ queries per type):
1. Create test set (10 queries per type)
2. Run all queries
3. Manually evaluate each
4. Calculate real accuracy
5. Compare to estimates

### Production Monitoring:
1. Track all queries
2. Collect user feedback
3. Measure satisfaction
4. Identify patterns
5. Continuously improve

---

## Bottom Line

**The percentages are:**
- ✅ **Educated estimates** based on:
  - Task complexity
  - LLM capabilities
  - Prompt quality
  - Industry standards
- ❌ **NOT tested results**
- ❌ **NOT guaranteed**
- ⚠️ **Subject to change** based on real testing

**What to do:**
1. **Test one query** of each type
2. **Evaluate quality** manually
3. **Adjust expectations** based on results
4. **Refine prompts** if needed
5. **Iterate** until quality is acceptable

**The estimates are a starting point, not a guarantee!**

