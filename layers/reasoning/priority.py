class PriorityAgent:
    """Agent 13: Triage Priority Map - Recommends resource allocation priority"""
    
    def __init__(self):
        self.severity_levels = ["low", "medium", "high", "critical"]
        self.priority_thresholds = {
            "low": (0.0, 0.5),
            "medium": (0.5, 0.7),
            "high": (0.7, 0.85),
            "critical": (0.85, 1.0)
        }
    
    def recommend(self, damage_mode, confidence_factor):
        """
        Recommends triage priority and resource allocation.
        
        Args:
            damage_mode: Most common damage severity from patterns
            confidence_factor: Confidence multiplier (0-2)
            
        Returns:
            Triage recommendation dictionary
        """
        try:
            # Map damage mode to base priority
            damage_to_priority = {
                "low": 1,
                "medium": 2,
                "high": 3,
                "critical": 4,
                "unknown": 2
            }
            
            base_priority = damage_to_priority.get(damage_mode.lower(), 2)
            
            # Apply confidence factor (can boost or reduce priority)
            adjusted_priority = min(4, max(1, base_priority * confidence_factor))
            
            # Determine priority level
            priority_level = "medium"
            for level, (min_val, max_val) in self.priority_thresholds.items():
                if min_val <= adjusted_priority / 4 < max_val:
                    priority_level = level
                    break
            
            recommendation = {
                "priority_level": priority_level,
                "priority_score": adjusted_priority / 4,
                "damage_severity": damage_mode,
                "confidence_adjusted": confidence_factor,
                "resource_allocation": self._get_resource_allocation(priority_level),
                "response_time_hours": self._get_response_time(priority_level),
                "triage_notes": f"Recommended priority: {priority_level.upper()} - "
                               f"Damage: {damage_mode}, Confidence: {confidence_factor:.2f}x"
            }
            return recommendation
        except Exception as e:
            print(f"Priority Agent Error: {e}")
            return {}
    
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