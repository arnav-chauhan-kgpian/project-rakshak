"""
Disaster Classification Agent - Zero-shot image classification.

Uses CLIP to classify whether an image shows disaster damage or is unrelated.
Acts as a gate before the main pipeline to reject non-disaster inputs.
"""

import os
from pathlib import Path
from typing import Dict, Optional
import numpy as np

class DisasterClassificationAgent:
    """
    Agent 0: Disaster Classification Gate
    Uses CLIP for zero-shot classification to determine if image is disaster-related.
    """
    
    # Candidate labels for classification
    DISASTER_LABELS = [
        "earthquake damage to buildings",
        "flood damage",
        "wildfire destruction",
        "hurricane damage",
        "tornado damage",
        "tsunami damage",
        "building collapse",
        "destroyed structures"
    ]
    
    NON_DISASTER_LABELS = [
        "normal city scene",
        "everyday photograph",
        "nature landscape",
        "people portrait",
        "indoor scene",
        "food photograph",
        "animal photograph"
    ]
    
    def __init__(self, confidence_threshold: float = 0.4):
        """
        Initialize the classifier.
        
        Args:
            confidence_threshold: Minimum confidence to classify as disaster (0-1)
        """
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.processor = None
        self._initialized = False
        
    def _lazy_init(self):
        """Lazy load CLIP model to avoid startup overhead."""
        if self._initialized:
            return
            
        try:
            from transformers import CLIPProcessor, CLIPModel
            import torch
            
            print("    Loading CLIP model for classification...")
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model.to(self.device)
            self._initialized = True
            print(f"    ✓ CLIP loaded on {self.device}")
        except Exception as e:
            print(f"    ⚠ CLIP initialization failed: {e}")
            self._initialized = False
    
    def classify(self, image_path: str) -> Dict:
        """
        Classify whether image shows disaster damage.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dict with:
                - is_disaster: bool
                - disaster_type: str (most likely disaster type or "none")
                - confidence: float (0-1)
                - all_scores: dict of label->score
        """
        self._lazy_init()
        
        if not self._initialized:
            # Fallback: assume disaster if model unavailable (to not block pipeline)
            return self._fallback_result(image_path)
        
        try:
            from PIL import Image
            import torch
            
            # Load image
            image = Image.open(image_path).convert("RGB")
            
            # Combine all labels
            all_labels = self.DISASTER_LABELS + self.NON_DISASTER_LABELS
            
            # Process inputs
            inputs = self.processor(
                text=all_labels,
                images=image,
                return_tensors="pt",
                padding=True
            ).to(self.device)
            
            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits_per_image = outputs.logits_per_image
                probs = logits_per_image.softmax(dim=1).cpu().numpy()[0]
            
            # Create score dict
            all_scores = {label: float(prob) for label, prob in zip(all_labels, probs)}
            
            # Calculate disaster vs non-disaster aggregate scores
            disaster_score = sum(probs[i] for i in range(len(self.DISASTER_LABELS)))
            non_disaster_score = sum(probs[i] for i in range(len(self.DISASTER_LABELS), len(all_labels)))
            
            # Find best disaster label
            disaster_probs = probs[:len(self.DISASTER_LABELS)]
            best_disaster_idx = np.argmax(disaster_probs)
            best_disaster_label = self.DISASTER_LABELS[best_disaster_idx]
            best_disaster_prob = float(disaster_probs[best_disaster_idx])
            
            # Map to disaster type
            disaster_type_map = {
                "earthquake damage to buildings": "earthquake",
                "flood damage": "flood",
                "wildfire destruction": "wildfire",
                "hurricane damage": "hurricane",
                "tornado damage": "tornado",
                "tsunami damage": "tsunami",
                "building collapse": "earthquake",
                "destroyed structures": "unknown"
            }
            
            is_disaster = disaster_score > non_disaster_score and disaster_score >= self.confidence_threshold
            
            return {
                "is_disaster": is_disaster,
                "disaster_type": disaster_type_map.get(best_disaster_label, "unknown") if is_disaster else "none",
                "confidence": disaster_score,
                "disaster_score": disaster_score,
                "non_disaster_score": non_disaster_score,
                "best_match": best_disaster_label if is_disaster else "non-disaster",
                "all_scores": all_scores
            }
            
        except Exception as e:
            print(f"    ⚠ Classification error: {e}")
            return self._fallback_result(image_path)
    
    def _fallback_result(self, image_path: str) -> Dict:
        """
        Fallback when model unavailable.
        Uses filename heuristics if available.
        """
        path = Path(image_path)
        filename = path.stem.lower()
        
        # Check for disaster keywords in filename
        disaster_keywords = ["disaster", "damage", "flood", "earthquake", "fire", "hurricane", "tsunami", "post"]
        is_disaster = any(kw in filename for kw in disaster_keywords)
        
        # Try to extract disaster type from filename
        disaster_type = "unknown"
        for dtype in ["earthquake", "flood", "wildfire", "hurricane", "tsunami", "volcano"]:
            if dtype in filename:
                disaster_type = dtype
                break
        
        print(f"    ⚠ Using filename heuristic: {'disaster' if is_disaster else 'non-disaster'}")
        
        return {
            "is_disaster": is_disaster,
            "disaster_type": disaster_type if is_disaster else "none",
            "confidence": 0.6 if is_disaster else 0.4,
            "disaster_score": 0.6 if is_disaster else 0.4,
            "non_disaster_score": 0.4 if is_disaster else 0.6,
            "best_match": "filename_heuristic",
            "all_scores": {},
            "fallback": True
        }
