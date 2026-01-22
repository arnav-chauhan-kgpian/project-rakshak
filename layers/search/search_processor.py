"""
SearchProcessorAgent: Unified Search Pre/Post Processing (Agents 5, 7, 8 Merged)
Handles query planning, cross-disaster penalties, and result validation in a single pass.
"""

import statistics
import math


class SearchProcessorAgent:
    """
    Unified agent for all search-related processing.
    Merges: QueryPlannerAgent (5), CrossDisasterAgent (7), RelevanceValidatorAgent (8).
    """
    
    def __init__(self):
        # Query planning configs (Agent 5)
        self.filter_strategies = {
            "earthquake": {"spatial_radius_km": 50, "temporal_days": 30, "severity_threshold": 0.6},
            "flood": {"spatial_radius_km": 100, "temporal_days": 14, "severity_threshold": 0.5},
            "wildfire": {"spatial_radius_km": 200, "temporal_days": 60, "severity_threshold": 0.4},
            "hurricane": {"spatial_radius_km": 300, "temporal_days": 45, "severity_threshold": 0.55},
            "volcano": {"spatial_radius_km": 80, "temporal_days": 45, "severity_threshold": 0.65},
            "tsunami": {"spatial_radius_km": 250, "temporal_days": 30, "severity_threshold": 0.7},
            "unknown": {"spatial_radius_km": 75, "temporal_days": 30, "severity_threshold": 0.5}
        }
        
        # Cross-disaster similarity (Agent 7)
        self.disaster_similarity = {
            ("earthquake", "earthquake"): 1.0, ("earthquake", "landslide"): 0.8,
            ("earthquake", "volcano"): 0.7, ("earthquake", "tsunami"): 0.6,
            ("flood", "flood"): 1.0, ("flood", "overflow"): 0.9,
            ("flood", "tsunami"): 0.7, ("flood", "hurricane"): 0.8,
            ("wildfire", "wildfire"): 1.0, ("wildfire", "smoke"): 0.7,
            ("hurricane", "hurricane"): 1.0, ("hurricane", "wind_damage"): 0.85,
            ("hurricane", "flood"): 0.7, ("hurricane", "tsunami"): 0.6,
            ("volcano", "volcano"): 1.0, ("volcano", "earthquake"): 0.7, ("volcano", "wildfire"): 0.5,
            ("tsunami", "tsunami"): 1.0, ("tsunami", "flood"): 0.8,
            ("tsunami", "earthquake"): 0.6, ("tsunami", "hurricane"): 0.5,
            ("unknown", "unknown"): 0.8
        }
        
        # Validator thresholds (Agent 8)
        self.score_threshold = 0.05
        self.required_results = 1
    
    # ===== Query Planning (Former Agent 5) =====
    def plan_query(self, latitude, longitude, disaster_type):
        """Plans search strategy based on disaster type."""
        strategy = self.filter_strategies.get(disaster_type, self.filter_strategies["earthquake"])
        return {
            "center_lat": latitude, "center_lon": longitude,
            "spatial_filter": {"type": "radius", "radius_km": strategy["spatial_radius_km"]},
            "temporal_filter": {"type": "recency", "days_back": strategy["temporal_days"]},
            "disaster_filter": disaster_type,
            "confidence_threshold": strategy["severity_threshold"],
            "max_results": 10, "search_mode": "hybrid"
        }
    
    # ===== Cross-Disaster Penalty (Former Agent 7) =====
    def apply_penalty(self, search_results, target_disaster_type):
        """Applies cross-disaster similarity penalties to scores."""
        refined_results = []
        for result in search_results:
            payload = result.get("payload") if isinstance(result, dict) else getattr(result, "payload", {})
            score = result.get("score") if isinstance(result, dict) else getattr(result, "score", 0)
            result_id = result.get("id") if isinstance(result, dict) else getattr(result, "id", None)
            
            result_disaster = (payload or {}).get("disaster_type", "unknown")
            penalty = self.disaster_similarity.get((target_disaster_type, result_disaster), 0.5)
            
            refined_results.append({
                "id": result_id,
                "score": (score or 0) * penalty,
                "original_score": score or 0,
                "penalty_factor": penalty,
                "payload": payload or {}
            })
        
        refined_results.sort(key=lambda x: x["score"], reverse=True)
        return refined_results
    
    # ===== Result Validation (Former Agent 8) =====
    def validate(self, search_results):
        """Validates search results quality."""
        if not search_results:
            return "REJECT", {"reason": "No results", "quality_score": 0.0}
        
        scores = [r["score"] for r in search_results]
        avg_score = statistics.mean(scores)
        result_count = len(scores)
        score_variance = statistics.variance(scores) if len(scores) > 1 else 0
        
        # Consistency bonus
        disaster_types = [r.get("payload", {}).get("disaster_type", "unknown") for r in search_results]
        type_counts = {}
        for dt in disaster_types:
            type_counts[dt] = type_counts.get(dt, 0) + 1
        consistency_ratio = max(type_counts.values()) / len(disaster_types) if disaster_types else 0
        
        # Quality score
        quality_score = avg_score + (consistency_ratio * 0.15) + min(0.1, math.log(result_count + 1) / 10) - min(0.1, score_variance * 0.5)
        quality_score = max(0.0, min(1.0, quality_score))
        
        # Geo diversity
        lats = [r.get("payload", {}).get("latitude", 0) for r in search_results]
        lons = [r.get("payload", {}).get("longitude", 0) for r in search_results]
        geo_diversity = min(1.0, ((max(lats) - min(lats)) + (max(lons) - min(lons))) / 20.0) if len(lats) > 1 else 0.0
        
        quality_metrics = {
            "result_count": result_count, "avg_score": avg_score,
            "median_score": statistics.median(scores), "max_score": max(scores),
            "score_variance": score_variance, "consistency_ratio": consistency_ratio,
            "geo_diversity": geo_diversity, "quality_score": quality_score,
            "score_breakdown": {"base": avg_score, "consistency_bonus": consistency_ratio * 0.15,
                               "count_bonus": min(0.1, math.log(result_count + 1) / 10),
                               "variance_penalty": -min(0.1, score_variance * 0.5)}
        }
        
        if avg_score < self.score_threshold or result_count < self.required_results:
            return "WARN", quality_metrics
        return "ACCEPT", quality_metrics
