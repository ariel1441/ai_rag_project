"""
High-End RAG System - No Compromises Version
For servers or high-end PCs with:
- 16GB+ RAM
- GPU support (optional but recommended)
- No memory limitations

This version uses:
- 4-bit quantization (best memory efficiency)
- Full model capabilities
- No workarounds or limitations
"""
import os
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    try:
        os.system('chcp 65001 >nul 2>&1')
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except:
        pass

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    import torch
except ImportError:
    pass

# Import base RAG system components
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.core.search import HybridSearch
from scripts.utils.query_parser import QueryParser
from scripts.utils.text_processing import combine_fields_with_weighting


class HighEndRAGSystem:
    """
    High-End RAG System - Optimal Configuration
    
    Designed for:
    - Servers with 16GB+ RAM
    - High-end PCs with GPU support
    - Production environments
    
    Features:
    - 4-bit quantization (4GB RAM usage)
    - GPU acceleration if available
    - No compromises or workarounds
    """
    
    def __init__(self, model_path=None):
        """Initialize high-end RAG system."""
        if model_path is None:
            base_path = Path(__file__).parent.parent.parent
            model_path = base_path / "models" / "llm" / "mistral-7b-instruct"
        
        self.model_path = str(model_path)
        self.model = None
        self.tokenizer = None
        self.search = None
        self.query_parser = QueryParser()
        
        print("High-End RAG System initialized")
        print(f"Model path: {self.model_path}")
    
    def connect_db(self):
        """Connect to database."""
        self.search = HybridSearch()
        print("✅ Database connected")
    
    def _has_gpu(self):
        """Check if GPU is available."""
        try:
            return torch.cuda.is_available()
        except:
            return False
    
    def load_model(self):
        """Load LLM model with optimal settings (4-bit quantization)."""
        if self.model is not None:
            return  # Already loaded
        
        print("Loading LLM model...")
        print("(This takes 30-60 seconds on first load)")
        
        # Load tokenizer
        print("Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_path,
            local_files_only=True
        )
        
        # Load model with 4-bit quantization (optimal for high-end systems)
        print("Loading model...")
        print("⚠️  Using 4-bit quantization (~4GB RAM)")
        print("   Best performance and memory efficiency")
        
        try:
            from transformers import BitsAndBytesConfig
            
            # 4-bit quantization config (optimal)
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
            
            # Determine device
            device_map = "auto"  # Use GPU if available, otherwise CPU
            if self._has_gpu():
                print("   GPU detected - using GPU acceleration")
            else:
                print("   No GPU - using CPU")
            
            print("⏳ Loading model (this takes 30-60 seconds, please wait)...")
            print("   Progress: Loading checkpoint shards...")
            sys.stdout.flush()
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                local_files_only=True,
                quantization_config=quantization_config,  # 4-bit quantization
                device_map=device_map,  # Auto (GPU if available)
                low_cpu_mem_usage=True
            )
            
            print("✅ Loaded with 4-bit quantization (~4GB RAM)")
            if self._has_gpu():
                print("   GPU acceleration enabled")
            
        except ImportError:
            raise ImportError(
                "bitsandbytes library required for 4-bit quantization.\n"
                "Install with: pip install bitsandbytes"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load model with 4-bit quantization: {e}\n"
                f"This version requires 4-bit quantization support.\n"
                f"For compatible version, use rag_query.py instead."
            )
        
        print("✅ Model loaded successfully")
    
    def query(self, user_query, top_k=20):
        """Execute full RAG query with optimal settings."""
        if self.model is None:
            self.load_model()
        
        if self.search is None:
            self.connect_db()
        
        # Parse query
        parsed = self.query_parser.parse(user_query)
        
        # Retrieve relevant requests
        requests = self.search.search(
            query_text=user_query,
            intent=parsed.get('intent'),
            entities=parsed.get('entities', {}),
            top_k=top_k
        )
        
        # Format context
        context = self._format_context(requests)
        
        # Generate answer
        answer = self._generate_answer(user_query, context)
        
        return {
            'answer': answer,
            'requests': requests,
            'intent': parsed.get('intent'),
            'entities': parsed.get('entities', {})
        }
    
    def _format_context(self, requests):
        """Format retrieved requests as context for LLM."""
        if not requests:
            return "לא נמצאו פניות רלוונטיות."
        
        context_parts = []
        for i, req in enumerate(requests[:10], 1):  # Top 10 for context
            text = combine_fields_with_weighting(req)
            context_parts.append(f"פנייה {i}:\n{text}")
        
        return "\n\n".join(context_parts)
    
    def _generate_answer(self, query, context):
        """Generate answer using LLM with optimal prompt."""
        # Build prompt using Mistral's chat template
        messages = [
            {
                "role": "system",
                "content": "אתה עוזר AI מקצועי שמסייע למשתמשים למצוא מידע על פניות במערכת. תן תשובות מדויקות, ברורות ובעברית."
            },
            {
                "role": "user",
                "content": f"הקשר:\n{context}\n\nשאלה: {query}\n\nתן תשובה מפורטת בעברית המבוססת על ההקשר לעיל."
            }
        ]
        
        # Apply chat template
        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt")
        
        # Move to device
        if self._has_gpu():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        # Decode
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract answer (remove prompt)
        if "תן תשובה" in generated_text:
            answer = generated_text.split("תן תשובה")[-1].strip()
        else:
            # Fallback: get everything after the last user message
            answer = generated_text.split(query)[-1].strip()
        
        # Clean up
        answer = answer.replace("<s>", "").replace("</s>", "").strip()
        
        return answer if answer else "לא הצלחתי ליצור תשובה."
    
    def close(self):
        """Clean up resources."""
        if self.model is not None:
            del self.model
            self.model = None
        if self.tokenizer is not None:
            del self.tokenizer
            self.tokenizer = None
        if self.search is not None:
            self.search.close()
            self.search = None

