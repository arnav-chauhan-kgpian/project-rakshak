import statistics

class RelevanceValidatorAgent:
    """Agent 8: Quality Validator - Assesses relevance and confidence of search results"""
    
    def __init__(self):
        # RRF fusion scores are small; accept low but non-zero evidence
        self.score_threshold = 0.05
        self.required_results = 1
    
    def validate(self, search_results):
        """
        Validates search results quality and relevance.
        
        Args:
            search_results: List of refined search results
            
        Returns:
            Tuple of (status, quality_metrics)
        """
        try:
            if not search_results:
                return "REJECT", {"reason": "No results found", "quality_score": 0.0}
            
            # Extract scores
            scores = [r["score"] for r in search_results]
            
            # Calculate quality metrics
            avg_score = statistics.mean(scores)
            median_score = statistics.median(scores)
            max_score = max(scores)
            result_count = len(scores)
            
            quality_metrics = {
                "result_count": result_count,
                "avg_score": avg_score,
                "median_score": median_score,
                "max_score": max_score,
                "score_variance": statistics.variance(scores) if len(scores) > 1 else 0,
                "quality_score": avg_score
            }
            
            # Validation rules
            if avg_score < self.score_threshold:
                return "WARN", quality_metrics
            
            if result_count < self.required_results:
                return "WARN", quality_metrics
            
            return "ACCEPT", quality_metrics
        except Exception as e:
            print(f"Validator Error: {e}")
            return "REJECT", {"error": str(e)}