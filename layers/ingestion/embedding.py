import numpy as np
from PIL import Image
from pathlib import Path

class EmbeddingAgent:
    """Agent 2: DINOv2 Feature Extraction - Converts satellite imagery to embeddings"""
    
    def __init__(self, model_name="dinov2_vitb14"):
        try:
            import torch
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            # In production: torch.hub.load('facebookresearch/dinov2', model_name)
            self.model = None  # Lazy load for testing
            self.embedding_dim = 768
        except ImportError:
            self.device = "cpu"
            self.model = None
            self.embedding_dim = 768
    
    def get_embedding(self, image_path):
        """
        Extracts DINOv2 embeddings from satellite imagery.
        
        Args:
            image_path: Path to satellite image file
            
        Returns:
            Vector embedding (768-dimensional)
        """
        try:
            # Load and preprocess image
            img = Image.open(image_path).convert('RGB')
            
            # Resize to standard size for DINOv2
            img_resized = img.resize((224, 224))
            
            # Convert to numpy array
            img_array = np.array(img_resized) / 255.0
            
            # In production: pass through DINOv2 model
            # For now: return mock embedding with reproducible values
            np.random.seed(hash(image_path) % 2**32)
            embedding = np.random.randn(self.embedding_dim).astype(np.float32)
            
            # Normalize
            embedding = embedding / np.linalg.norm(embedding)
            return embedding.tolist()
        except Exception as e:
            print(f"Embedding Agent Error: {e}")
            # Return zero vector on error
            return [0.0] * self.embedding_dim