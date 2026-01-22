import statistics
import math

class RelevanceValidatorAgent:
    """Agent 8: Quality Validator - Assesses relevance and confidence of search results"""
    
    def __init__(self):
        # RRF fusion scores are small; require meaningful evidence
        # Increased thresholds to prevent over-confident results from sparse data
        self.score_threshold = 0.08  # Raised from 0.05 for stricter validation
        self.required_results = 3    # Raised from 1 to require more corroborating evidence
        
        # Absolute similarity threshold: reject if best match is below this value
        # This prevents processing images that don't match any known disasters
        self.absolute_similarity_threshold = 0.35
    
    def validate(self, search_results):
        """
        Validates search results quality and relevance with enhanced scoring.
        
        Args:
            search_results: List of refined search results
            
        Returns:
            Tuple of (status, quality_metrics)
        """
        try:
            if not search_results:
                return "REJECT", {
                    "reason": "No results found",
                    "quality_score": 0.0,
                    "suggestion": "Run 'python main.py --batch-ingest' to populate the database with xBD disaster data"
                }
            
            # Extract scores
            scores = [r["score"] for r in search_results]
            
            # Calculate base quality metrics
            avg_score = statistics.mean(scores)
            median_score = statistics.median(scores)
            max_score = max(scores)
            result_count = len(scores)
            score_variance = statistics.variance(scores) if len(scores) > 1 else 0
            
            # ===== Enhanced Quality Scoring =====
            
            # 1. Base quality from average score
            base_quality = avg_score
            
            # 2. Consistency bonus: boost if results agree on disaster type
            disaster_types = [r.get("payload", {}).get("disaster_type", "unknown") for r in search_results]
            type_counts = {}
            for dt in disaster_types:
                type_counts[dt] = type_counts.get(dt, 0) + 1
            most_common_count = max(type_counts.values()) if type_counts else 0
            consistency_ratio = most_common_count / len(disaster_types) if disaster_types else 0
            consistency_bonus = consistency_ratio * 0.15  # Up to 15% bonus for consistency
            
            # 3. Variance penalty: reduce score for inconsistent results
            variance_penalty = min(0.1, score_variance * 0.5)  # Cap at 10% penalty
            
            # 4. Result count bonus (logarithmic, diminishing returns)
            count_bonus = min(0.1, math.log(result_count + 1) / 10)  # Up to 10% for many results
            
            # 5. Geographic diversity factor (check if results span different areas)
            geo_diversity = self._calculate_geo_diversity(search_results)
            
            # Final quality score
            quality_score = base_quality + consistency_bonus + count_bonus - variance_penalty
            quality_score = max(0.0, min(1.0, quality_score))  # Clamp to [0, 1]
            
            quality_metrics = {
                "result_count": result_count,
                "avg_score": avg_score,
                "median_score": median_score,
                "max_score": max_score,
                "score_variance": score_variance,
                "consistency_ratio": consistency_ratio,
                "geo_diversity": geo_diversity,
                "quality_score": quality_score,
                # Breakdown for transparency
                "score_breakdown": {
                    "base": base_quality,
                    "consistency_bonus": consistency_bonus,
                    "count_bonus": count_bonus,
                    "variance_penalty": -variance_penalty
                }
            }
            
            # Validation rules
            
            # ABSOLUTE THRESHOLD: Reject if best match is too dissimilar
            # This catches cases where input image has no related disasters in DB
            if max_score < self.absolute_similarity_threshold:
                quality_metrics["rejection_reason"] = "no_similar_disasters"
                return "REJECT", {
                    **quality_metrics,
                    "reason": f"No similar disasters found (max_score={max_score:.3f} < threshold={self.absolute_similarity_threshold})",
                    "suggestion": "This image may not show disaster damage, or no similar disaster types exist in the database"
                }
            
            if avg_score < self.score_threshold:
                return "WARN", quality_metrics
            
            if result_count < self.required_results:
                return "WARN", quality_metrics
            
            return "ACCEPT", quality_metrics
        except Exception as e:
            print(f"Validator Error: {e}")
            return "REJECT", {"error": str(e)}
    
    def _calculate_geo_diversity(self, results):
        """Calculate geographic spread of results (0-1 score)."""
        try:
            lats = [r.get("payload", {}).get("latitude", 0) for r in results]
            lons = [r.get("payload", {}).get("longitude", 0) for r in results]
            
            if len(lats) < 2:
                return 0.0
            
            lat_spread = max(lats) - min(lats)
            lon_spread = max(lons) - min(lons)
            
            # Normalize spread (assume max spread of ~10 degrees is high diversity)
            diversity = min(1.0, (lat_spread + lon_spread) / 20.0)
            return diversity
        except:
            return 0.0