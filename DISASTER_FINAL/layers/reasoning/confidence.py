import math

class ConfidenceControllerAgent:
    """Agent 11: Confidence Score Controller - Calibrates final confidence scores"""
    
    def __init__(self):
        self.base_calibration = 0.7
    
    def calculate(self, vector_score, evidence_quality_score, quality_metrics=None):
        """
        Calculates calibrated confidence score with enhanced factors.
        
        Args:
            vector_score: Vector similarity score (0-1)
            evidence_quality_score: Quality of supporting evidence (0-1)
            quality_metrics: Optional dict with additional scoring factors
            
        Returns:
            Calibrated confidence score (0-1)
        """
        try:
            # Base weights
            weights = {
                "vector_similarity": 0.5,
                "evidence_quality": 0.3,
                "additional_factors": 0.2
            }
            
            # Calculate additional factors from quality_metrics
            additional_score = 0.5  # Default
            if quality_metrics:
                # Factor in result count (logarithmic, max out around 10 results)
                result_count = quality_metrics.get("result_count", 1)
                count_factor = min(1.0, math.log(result_count + 1) / math.log(11))
                
                # Factor in consistency (results agreeing on disaster type)
                consistency = quality_metrics.get("consistency_ratio", 0.5)
                
                # Variance penalty (high variance = less confidence)
                variance = quality_metrics.get("score_variance", 0)
                variance_penalty = min(0.3, variance * 0.5)
                
                additional_score = (count_factor * 0.4 + consistency * 0.4 + (1 - variance_penalty) * 0.2)
            
            # Weighted combination
            combined_score = (
                vector_score * weights["vector_similarity"] +
                evidence_quality_score * weights["evidence_quality"] +
                additional_score * weights["additional_factors"]
            )
            
            # Apply calibration (slightly compress extreme values)
            calibrated = (
                self.base_calibration +
                (combined_score - 0.5) * (1 - 2 * abs(self.base_calibration - 0.5))
            )
            
            # Clamp to [0, 0.95] - hard ceiling to prevent over-confidence
            # Even with perfect input scores, we cap at 95% to acknowledge uncertainty
            return max(0.0, min(0.95, calibrated))
        except Exception as e:
            print(f"Confidence Controller Error: {e}")
            return 0.5