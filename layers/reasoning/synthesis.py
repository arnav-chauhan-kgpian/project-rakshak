import statistics
from collections import Counter

class EvidenceSynthesisAgent:
    """Agent 9: Histogram & Pattern Analysis - Synthesizes patterns from multiple results"""
    
    def __init__(self):
        pass
    
    def analyze_patterns(self, search_results):
        """
        Analyzes patterns and creates histogram of disaster characteristics.
        
        Args:
            search_results: List of validated search results
            
        Returns:
            Dictionary with pattern analysis
        """
        try:
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
            return {}