class CrossDisasterAgent:
    """Agent 7: Cross-Disaster Transfer Learning - Applies penalty/boost logic based on disaster type"""
    
    def __init__(self):
        # Penalty multipliers for cross-disaster relevance
        self.disaster_similarity = {
            # Earthquake family
            ("earthquake", "earthquake"): 1.0,
            ("earthquake", "landslide"): 0.8,
            ("earthquake", "volcano"): 0.7,
            ("earthquake", "tsunami"): 0.6,
            
            # Flood family
            ("flood", "flood"): 1.0,
            ("flood", "overflow"): 0.9,
            ("flood", "tsunami"): 0.7,
            ("flood", "hurricane"): 0.8,
            
            # Wildfire family
            ("wildfire", "wildfire"): 1.0,
            ("wildfire", "smoke"): 0.7,
            
            # Hurricane family
            ("hurricane", "hurricane"): 1.0,
            ("hurricane", "wind_damage"): 0.85,
            ("hurricane", "flood"): 0.7,
            ("hurricane", "tsunami"): 0.6,
            
            # Volcano family
            ("volcano", "volcano"): 1.0,
            ("volcano", "earthquake"): 0.7,
            ("volcano", "wildfire"): 0.5,
            
            # Tsunami family
            ("tsunami", "tsunami"): 1.0,
            ("tsunami", "flood"): 0.8,
            ("tsunami", "earthquake"): 0.6,
            ("tsunami", "hurricane"): 0.5,
            
            # Unknown fallback
            ("unknown", "unknown"): 0.8
        }
    
    def apply_penalty(self, search_results, target_disaster_type):
        """
        Applies transfer learning penalties/boosts based on disaster type similarity.
        
        Args:
            search_results: List of search results from hybrid_search
            target_disaster_type: The disaster type we're analyzing
            
        Returns:
            Refined search results with adjusted scores
        """
        try:
            refined_results = []
            
            for result in search_results:
                # Support both dict and ScoredPoint inputs
                payload = result.get("payload") if isinstance(result, dict) else getattr(result, "payload", {})
                score = result.get("score") if isinstance(result, dict) else getattr(result, "score", 0)
                result_id = result.get("id") if isinstance(result, dict) else getattr(result, "id", None)

                result_disaster = (payload or {}).get("disaster_type", "unknown")
                
                # Get similarity penalty
                penalty_key = (target_disaster_type, result_disaster)
                penalty = self.disaster_similarity.get(
                    penalty_key,
                    0.5  # Default low penalty for very different disasters
                )
                
                # Apply penalty to score
                original_score = score or 0
                adjusted_score = original_score * penalty
                
                # Create refined result
                refined_result = {
                    "id": result_id,
                    "score": adjusted_score,
                    "original_score": original_score,
                    "penalty_factor": penalty,
                    "payload": payload or {}
                }
                refined_results.append(refined_result)
            
            # Sort by adjusted score
            refined_results.sort(key=lambda x: x["score"], reverse=True)
            return refined_results
        except Exception as e:
            print(f"Cross-Disaster Transfer Error: {e}")
            return search_results