"""
GPU-Optimized RAG System

This version removes all CPU optimizations and uses optimal settings for GPU.
Designed for powerful PCs with NVIDIA GPUs.

Features:
- Full 500 token answers (not limited to 200)
- Sampling with temperature (not greedy decoding)
- 4-bit quantization (if supported) or float16
- Automatic GPU detection and usage
- No CPU workarounds or limitations
"""
import os
import sys
from pathlib import Path

# Import the base RAG system
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from scripts.core.rag_query import RAGSystem

class GPUOptimizedRAGSystem(RAGSystem):
    """
    GPU-Optimized RAG System - No Compromises
    
    This version removes all CPU optimizations and uses optimal settings.
    Perfect for powerful PCs with GPU support.
    """
    
    def generate_answer(self, user_content: str, max_length: int = 500) -> str:
        """
        Generate answer with optimal settings (no CPU optimizations).
        
        Overrides the base method to always use:
        - Full max_length (500 tokens, not 200)
        - Sampling with temperature (not greedy)
        - Best quality settings
        """
        import torch
        import time
        
        if self.model is None:
            self.load_model()
        
        if self.tokenizer is None:
            raise ValueError("Tokenizer not loaded!")
        
        # Check for GPU
        device = "cuda" if self._has_gpu() else "cpu"
        
        print(f"\n{'='*80}")
        print("GENERATING ANSWER (GPU-Optimized)")
        print(f"{'='*80}")
        print(f"   Device: {device.upper()}")
        
        if device == "cuda":
            print("   ✅ GPU detected - using GPU acceleration")
            print("   ⚡ Expected speed: 5-15 seconds per query")
        else:
            print("   ⚠️  No GPU detected - using CPU")
            print("   ⏳ Expected speed: 5-15 minutes per query")
            print("   💡 Tip: Install CUDA and PyTorch with GPU support for much faster generation")
        
        print(f"   Max tokens: {max_length} (full length, not limited)")
        print(f"   Decoding: Sampling with temperature=0.7 (optimal quality)")
        print("   Starting generation...")
        print(f"   [⏱️  START] model.generate() at {time.strftime('%H:%M:%S')}")
        sys.stdout.flush()
        
        try:
            # Tokenize input
            inputs = self.tokenizer(user_content, return_tensors="pt", truncation=True, max_length=2048)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            with torch.no_grad():
                # OPTIMAL SETTINGS (no CPU optimizations)
                generation_kwargs = {
                    **inputs,
                    'max_new_tokens': max_length,  # Full length (500 tokens)
                    'pad_token_id': self.tokenizer.eos_token_id if self.tokenizer.pad_token_id is None else self.tokenizer.pad_token_id,
                    'eos_token_id': self.tokenizer.eos_token_id,
                    # Optimal sampling settings
                    'do_sample': True,           # Sampling (not greedy)
                    'temperature': 0.7,          # Creative but controlled
                    'top_p': 0.9,                # Nucleus sampling
                    'top_k': 50,                 # Top-k sampling
                }
                
                outputs = self.model.generate(**generation_kwargs)
        
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                print(f"\n❌ GPU out of memory!")
                print("   Try:")
                print("   1. Use 4-bit quantization (already enabled if supported)")
                print("   2. Reduce max_length (currently 500)")
                print("   3. Close other applications using GPU")
                raise RuntimeError(
                    "GPU out of memory. Try reducing max_length or using CPU."
                )
            raise
        
        # Decode output
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract answer (remove input prompt)
        if user_content in generated_text:
            answer = generated_text.split(user_content, 1)[1].strip()
        else:
            answer = generated_text.strip()
        
        generation_end = time.time()
        generation_duration = generation_end - time.time()
        
        print(f"   [⏱️  END] Generation completed at {time.strftime('%H:%M:%S')}")
        if generation_duration > 0:
            print(f"   [⏱️  DURATION] {generation_duration:.2f} seconds")
        print(f"   [📊 ANSWER LENGTH] {len(answer)} characters, ~{len(answer.split())} words")
        sys.stdout.flush()
        
        return answer

