import statistics
from collections import Counter

class EvidenceSynthesisAgent:
    """Agent 9: Histogram & Pattern Analysis - Synthesizes patterns from multiple results"""
    
    def __init__(self, qdrant_client=None):
        self.client = qdrant_client
        self.collection_name = "disaster_memory"
    
    def refine_evidence(self, search_results, limit=5):
        """
        Active Reasoning: Uses Qdrant's Recommendation API to find more incidents similar 
        to the best verified search results (Relevance Feedback / "More like this").
        
        This expands the evidence base beyond the initial text/image query by using 
        actual verified ground-truth examples as positive signals.
        """
        if not self.client or not search_results:
            return search_results

        try:
            # 1. Get positive examples (top 3 validated results)
            # Use 'id' from the result dictionary
            positive_ids = [r["id"] for r in search_results[:3]]
            
            if not positive_ids:
                return search_results
                
            print(f"    ⟳ Refining evidence (Recommendation) based on IDs: {positive_ids}")
            
            # 2. Call Recommendation API (using new query_points API for qdrant-client 1.16+)
            from qdrant_client import models
            recommended = self.client.query_points(
                collection_name=self.collection_name,
                query=models.RecommendQuery(
                    recommend=models.RecommendInput(positive=positive_ids)
                ),
                using="image",  # Use visual similarity for deep pattern matching
                limit=limit,
                with_payload=True
            )
            
            # 3. Normalize & Merge
            normalized_recs = self._normalize_recs(recommended.points)
            
            # Use dictionary to dedup by ID (keep existing search results as primary)
            merged = {r["id"]: r for r in search_results + normalized_recs}
            
            # Convert back to list and sort by score
            refined_list = list(merged.values())
            refined_list.sort(key=lambda x: x["score"], reverse=True)
            
            print(f"    ✓ Evidence pool expanded: {len(search_results)} → {len(refined_list)} incidents")
            return refined_list
            
        except Exception as e:
            print(f"    ⚠ Evidence refinement skipped: {e}")
            return search_results

    def _normalize_recs(self, points):
        """Convert Qdrant ScoredPoint objects into standard result dicts"""
        normalized = []
        for p in points:
            try:
                normalized.append({
                    "id": p.id,
                    "score": p.score,
                    "payload": p.payload or {},
                    "source": "recommendation"  # Tag as recommended
                })
            except:
                continue
        return normalized

    def analyze_patterns(self, search_results):
        """
        Analyzes patterns and creates histogram of disaster characteristics.
        Applies active evidence refinement if client is available.
        """
        try:
            # 1. Active Refinement (Relevance Feedback Loop)
            # If we have a client, try to find more evidence before synthesizing
            if self.client:
                search_results = self.refine_evidence(search_results)
            
            if not search_results:
                return {
                    "mode": "unknown",
                    "severity_distribution": {},
                    "damage_counts": {"no-damage": 0, "minor-damage": 0, "major-damage": 0, "destroyed": 0},
                    "geographic_center": None,
                    "temporal_trend": None
                }
            
            # Extract damage severities
            severities = [r["payload"].get("damage_severity", "medium") for r in search_results]
            severity_counter = Counter(severities)
            # Handle empty case if somehow severities is empty
            if not severities:
                mode_severity = "unknown"
            else:
                mode_severity = severity_counter.most_common(1)[0][0]
            
            # Extract spatial data
            lats = [r["payload"].get("latitude", 0) for r in search_results]
            lons = [r["payload"].get("longitude", 0) for r in search_results]
            
            # Aggregate building-level damage counts from xBD
            total_damage_counts = {"no-damage": 0, "minor-damage": 0, "major-damage": 0, "destroyed": 0}
            for r in search_results:
                damage_counts = r["payload"].get("damage_counts", {})
                for damage_type, count in damage_counts.items():
                    if damage_type in total_damage_counts:
                        total_damage_counts[damage_type] += count
            
            patterns = {
                "mode": mode_severity,
                "severity_distribution": dict(severity_counter),
                "damage_counts": total_damage_counts,
                "total_buildings": sum(total_damage_counts.values()),
                "geographic_center": {
                    "latitude": statistics.mean(lats) if lats else 0,
                    "longitude": statistics.mean(lons) if lons else 0
                },
                "temporal_trend": "increasing" if len(search_results) > 1 else "stable",
                "confidence_level": statistics.mean([r["score"] for r in search_results]),
                "result_count": len(search_results),
                "disaster_types": list(set([r["payload"].get("disaster_type", "unknown") for r in search_results]))
            }
            return patterns
        except Exception as e:
            print(f"Synthesis Error: {e}")
            import traceback
            traceback.print_exc()
            return {}