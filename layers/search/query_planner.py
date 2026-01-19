class QueryPlannerAgent:
    """Agent 5: Query Filter Configuration - Plans search strategy with spatial/temporal filters"""
    
    def __init__(self):
        self.filter_strategies = {
            "earthquake": {"spatial_radius_km": 50, "temporal_days": 30, "severity_threshold": 0.6},
            "flood": {"spatial_radius_km": 100, "temporal_days": 14, "severity_threshold": 0.5},
            "wildfire": {"spatial_radius_km": 200, "temporal_days": 60, "severity_threshold": 0.4},
            "hurricane": {"spatial_radius_km": 300, "temporal_days": 45, "severity_threshold": 0.55},
            "volcano": {"spatial_radius_km": 80, "temporal_days": 45, "severity_threshold": 0.65},
            "tsunami": {"spatial_radius_km": 250, "temporal_days": 30, "severity_threshold": 0.7},
            "unknown": {"spatial_radius_km": 75, "temporal_days": 30, "severity_threshold": 0.5}
        }
    
    def plan_query(self, latitude, longitude, disaster_type):
        """
        Plans search strategy based on disaster type and location.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            disaster_type: Type of disaster
            
        Returns:
            Dictionary with search parameters
        """
        try:
            strategy = self.filter_strategies.get(disaster_type, self.filter_strategies["earthquake"])
            
            plan = {
                "center_lat": latitude,
                "center_lon": longitude,
                "spatial_filter": {
                    "type": "radius",
                    "radius_km": strategy["spatial_radius_km"]
                },
                "temporal_filter": {
                    "type": "recency",
                    "days_back": strategy["temporal_days"]
                },
                "disaster_filter": disaster_type,
                "confidence_threshold": strategy["severity_threshold"],
                "max_results": 10,
                "search_mode": "hybrid"  # Vector + metadata filters
            }
            return plan
        except Exception as e:
            print(f"Query Planner Error: {e}")
            return {}