import numpy as np
from PIL import Image
from pathlib import Path
import threading

class EmbeddingAgent:
    """Agent 2: DINOv2 Feature Extraction - Converts satellite imagery to embeddings
    
    Uses the real DINOv2 Vision Transformer model from Meta AI to extract
    768-dimensional feature vectors that capture visual semantics of disaster imagery.
    """
    
    def __init__(self, model_name="facebook/dinov2-base"):
        """Initialize DINOv2 model.
        
        Args:
            model_name: HuggingFace model name (default: facebook/dinov2-base)
        """
        self.embedding_dim = 768
        self.model = None
        self.processor = None
        self.device = None
        self.model_name = model_name
        self._initialized = False
        self._lock = threading.Lock()
        
    def _lazy_init(self):
        """Lazy initialization of model to avoid slow startup (Thread-Safe)."""
        if self._initialized:
            return
            
        with self._lock:
            if self._initialized:
                return
                
            try:
                import torch
                # Try newer import first, fallback to older
                try:
                    from transformers import AutoImageProcessor as ImageProcessor
                except ImportError:
                    from transformers import AutoFeatureExtractor as ImageProcessor
                from transformers import AutoModel
                
                print("  Loading DINOv2 model (first run downloads ~350MB)...")
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                
                # Load processor
                self.processor = ImageProcessor.from_pretrained(self.model_name)
                
                # Load model standard way (safer than device_map="auto" for this model size)
                if torch.cuda.is_available():
                    print("  Using GPU for DINOv2...")
                    self.model = AutoModel.from_pretrained(self.model_name)
                    self.model.to(self.device)
                    self.model.half() # Use half precision on GPU
                else:
                    self.model = AutoModel.from_pretrained(self.model_name)
                    self.model.to(self.device)
                
                self.model.eval()
                
                device_name = "GPU" if torch.cuda.is_available() else "CPU"
                print(f"  ✓ DINOv2 loaded on {device_name}")
                self._initialized = True
                
            except ImportError as e:
                print(f"  ⚠ DINOv2 dependencies missing: {e}")
                print("  Install with: pip install torch transformers")
                self._initialized = False
            except Exception as e:
                print(f"  ⚠ DINOv2 initialization error: {e}")
                self._initialized = False
    
    def get_embedding(self, image_path):
        """
        Extracts DINOv2 embeddings from satellite imagery.
        
        Args:
            image_path: Path to satellite image file
            
        Returns:
            Vector embedding (768-dimensional list of floats)
        """
        try:
            # Lazy load model on first use
            self._lazy_init()
            
            # Load and preprocess image
            img_path = Path(image_path)
            if not img_path.exists():
                print(f"    ⚠ Image not found: {image_path}")
                return self._fallback_embedding(image_path)
            
            img = Image.open(image_path).convert('RGB')
            
            # If model loaded successfully, use real DINOv2
            if self._initialized and self.model is not None:
                return self._extract_real_embedding(img)
            else:
                # Fallback to deterministic mock
                return self._fallback_embedding(image_path)
                
        except Exception as e:
            print(f"  Embedding Agent Error: {e}")
            return self._fallback_embedding(image_path)
    
    def _extract_real_embedding(self, img):
        """Extract embedding using real DINOv2 model."""
        import torch
        
        # Process image
        inputs = self.processor(images=img, return_tensors="pt")
        # Move to device and cast if needed
        model_dtype = next(self.model.parameters()).dtype
        inputs = {k: v.to(self.device).to(model_dtype) for k, v in inputs.items()}
        
        # Extract features
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use CLS token embedding (first token)
            embedding = outputs.last_hidden_state[:, 0, :].squeeze()
        
        # Convert to numpy and normalize
        embedding = embedding.cpu().numpy().astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
    
    def _fallback_embedding(self, image_path):
        """Fallback: deterministic mock embedding when model unavailable."""
        import os
        if os.getenv("PRODUCTION_MODE", "").lower() == "true":
            raise RuntimeError(f"DINOv2 model failed to load in production mode. Cannot process: {image_path}")
        print(f"    ⚠ Using fallback embedding (DINOv2 unavailable)")
        np.random.seed(hash(str(image_path)) % 2**32)
        embedding = np.random.randn(self.embedding_dim).astype(np.float32)
        embedding = embedding / np.linalg.norm(embedding)
        return embedding.tolist()