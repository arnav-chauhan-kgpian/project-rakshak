class ConfidenceControllerAgent:
    """Agent 11: Confidence Score Controller - Calibrates final confidence scores"""
    
    def __init__(self):
        self.base_calibration = 0.7
    
    def calculate(self, vector_score, evidence_quality_score):
        """
        Calculates calibrated confidence score.
        
        Args:
            vector_score: Vector similarity score (0-1)
            evidence_quality_score: Quality of supporting evidence (0-1)
            
        Returns:
            Calibrated confidence score (0-1)
        """
        try:
            # Weighted combination
            weights = {
                "vector_similarity": 0.6,
                "evidence_quality": 0.4
            }
            
            combined_score = (
                vector_score * weights["vector_similarity"] +
                evidence_quality_score * weights["evidence_quality"]
            )
            
            # Apply calibration (slightly compress extreme values)
            calibrated = (
                self.base_calibration +
                (combined_score - 0.5) * (1 - 2 * abs(self.base_calibration - 0.5))
            )
            
            # Clamp to [0, 1]
            return max(0.0, min(1.0, calibrated))
        except Exception as e:
            print(f"Confidence Controller Error: {e}")
            return 0.5