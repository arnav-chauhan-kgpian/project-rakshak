from qdrant_client import models
from typing import Optional, Dict, Any, List

class PriorityAgent:
    """Agent 13: Triage Priority Map - Recommends resource allocation priority using Hybrid RAG"""
    
    def __init__(self, qdrant_client=None):
        self.client = qdrant_client
        self.collection_name = "disaster_memory"
        self.severity_levels = ["low", "medium", "high", "critical"]
        self.priority_thresholds = {
            "low": (0.0, 0.5),
            "medium": (0.5, 0.7),
            "high": (0.7, 0.85),
            "critical": (0.85, 1.0)
        }
        self.level_map = {"low": 1, "medium": 2, "high": 3, "critical": 4, "unknown": 2}
    
    def recommend(self, damage_mode: str, confidence_factor: float, incident_embedding: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Recommends triage priority and resource allocation.
        Uses Hybrid strategy: Rule-based base + RAG-based adjustment from history.
        
        Args:
            damage_mode: Most common damage severity
            confidence_factor: Confidence multiplier
            incident_embedding: Current incident vector for RAG lookup
            
        Returns:
            Triage recommendation dictionary
        """
        try:
            # 1. Rule-Based Score (Base Truth)
            base_val = self.level_map.get(damage_mode.lower(), 2)
            rule_score = min(4, max(1, base_val * confidence_factor))
            
            rag_note = ""
            final_score = rule_score
            
            # 2. RAG-Based Score (Historical Wisdom)
            # If we have the client and embedding, look up what we did in similar past cases
            if self.client and incident_embedding:
                rag_score = self._get_history_consensus(incident_embedding)
                if rag_score:
                    # Blend: 60% Current Rule + 40% History
                    # This smooths out anomalies while respecting the current damage assessment
                    final_score = (0.6 * rule_score) + (0.4 * rag_score)
                    rag_note = f" (Refined by {rag_score:.1f} hist avg)"
            
            # 3. Determine Final Level
            # Normalize 1-4 scale to 0-1 for thresholds
            normalized_score = final_score / 4.0
            
            priority_level = "medium"
            for level, (min_val, max_val) in self.priority_thresholds.items():
                if min_val <= normalized_score < max_val:
                    priority_level = level
                    break
            
            # Clamp critical
            if normalized_score >= 0.85:
                priority_level = "critical"
            
            recommendation = {
                "priority_level": priority_level,
                "priority_score": normalized_score,
                "damage_severity": damage_mode,
                "confidence_adjusted": confidence_factor,
                "resource_allocation": self._get_resource_allocation(priority_level),
                "response_time_hours": self._get_response_time(priority_level),
                "triage_notes": f"Recommended priority: {priority_level.upper()}{rag_note} - "
                               f"Damage: {damage_mode}, Conf: {confidence_factor:.2f}x"
            }
            return recommendation
            
        except Exception as e:
            print(f"Priority Agent Error: {e}")
            return self._fallback_recommendation(damage_mode, confidence_factor)

    def _get_history_consensus(self, embedding: List[float]) -> Optional[float]:
        """Query Qdrant for similar past resolved incidents and average their priority."""
        try:
            # Search for 'history' items with valid priority levels
            # We filter by 'history' type to ensure we are looking at past records
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=embedding,
                using="image",
                query_filter=models.Filter(
                    must=[
                        models.FieldCondition(key="type", match=models.MatchValue(value="history")),
                    ]
                ),
                limit=5,
            ).points
            
            if not results:
                return None
            
            scores = []
            for hit in results:
                # Extract priority from payload
                if hit.payload and "metadata" in hit.payload:
                    # Metadata structure from memory_store: metadata={"priority_level": ...}
                    meta = hit.payload.get("metadata", {})
                    p_level = meta.get("priority_level")
                    if p_level and p_level in self.level_map:
                        scores.append(self.level_map[p_level])
            
            if not scores:
                return None
                
            return sum(scores) / len(scores)
            
        except Exception as e:
            print(f"Priority RAG lookup failed: {e}")
            return None
    
    def _fallback_recommendation(self, damage_mode, confidence_factor):
        """Fallback if main logic fails"""
        return {
            "priority_level": "medium",
            "priority_score": 0.5,
            "damage_severity": damage_mode,
            "triage_notes": "Fallback recommendation (Error in PriorityAgent)"
        }

    def _get_resource_allocation(self, priority_level):
        """Maps priority level to resource allocation percentage."""
        allocation = {
            "low": {"personnel": 10, "vehicles": 2, "funds_percent": 5},
            "medium": {"personnel": 30, "vehicles": 6, "funds_percent": 15},
            "high": {"personnel": 60, "vehicles": 15, "funds_percent": 35},
            "critical": {"personnel": 100, "vehicles": 30, "funds_percent": 100}
        }
        return allocation.get(priority_level, allocation["medium"])
    
    def _get_response_time(self, priority_level):
        """Maps priority level to recommended response time in hours."""
        response_times = {
            "low": 72,
            "medium": 24,
            "high": 6,
            "critical": 1
        }
        return response_times.get(priority_level, 24)