"""
Agent 9b: Geographic Similarity Search
Finds historical disasters that occurred at similar geographic locations.
Uses Qdrant's geo-radius filtering to find events within a specified radius.
"""

from qdrant_client import models


class GeoSimilarityAgent:
    """Agent 9b: Finds disasters at similar geographic locations"""
    
    def __init__(self, qdrant_client):
        self.client = qdrant_client
        self.collection_name = "disaster_memory"
    
    def find_nearby_disasters(self, latitude, longitude, radius_km=100, limit=5, exclude_incident_id=None):
        """
        Find historical disasters within a geographic radius.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude  
            radius_km: Search radius in kilometers (default 100km)
            limit: Max results to return
            exclude_incident_id: Current incident to exclude from results
            
        Returns:
            List of nearby historical disasters
        """
        try:
            # Build filter conditions
            filter_conditions = []
            must_not_conditions = []
            
            # Exclude current incident
            if exclude_incident_id:
                must_not_conditions.append(
                    models.FieldCondition(
                        key="incident_id",
                        match=models.MatchValue(value=exclude_incident_id)
                    )
                )
            
            # Geo radius filter - find points within radius_km of the location
            geo_filter = models.FieldCondition(
                key="location",  # Assuming we store geo points
                geo_radius=models.GeoRadius(
                    center=models.GeoPoint(lat=latitude, lon=longitude),
                    radius=radius_km * 1000  # Convert km to meters
                )
            )
            filter_conditions.append(geo_filter)
            
            query_filter = models.Filter(
                must=filter_conditions if filter_conditions else None,
                must_not=must_not_conditions if must_not_conditions else None
            )
            
            # Use scroll to get points matching the geo filter
            results, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=query_filter,
                limit=limit,
                with_payload=True
            )
            
            # Normalize results
            normalized = []
            for point in results:
                normalized.append({
                    "id": point.id,
                    "score": 1.0,  # Geo matches don't have similarity scores
                    "payload": point.payload or {},
                    "source": "geo_similarity"
                })
            
            print(f"    ✓ Found {len(normalized)} disasters within {radius_km}km radius")
            return normalized
            
        except Exception as e:
            # Fallback: If geo field doesn't exist, search by lat/lon range
            print(f"    ⚠ Geo filter failed ({e}), using lat/lon range fallback...")
            return self._fallback_search(latitude, longitude, radius_km, limit, exclude_incident_id)
    
    def _fallback_search(self, latitude, longitude, radius_km, limit, exclude_incident_id):
        """
        Fallback search using lat/lon range filters when geo field is unavailable.
        """
        try:
            # Approximate degree range (1 degree ≈ 111km)
            degree_range = radius_km / 111.0
            
            filter_conditions = [
                models.FieldCondition(
                    key="latitude",
                    range=models.Range(
                        gte=latitude - degree_range,
                        lte=latitude + degree_range
                    )
                ),
                models.FieldCondition(
                    key="longitude", 
                    range=models.Range(
                        gte=longitude - degree_range,
                        lte=longitude + degree_range
                    )
                )
            ]
            
            must_not = []
            if exclude_incident_id:
                must_not.append(
                    models.FieldCondition(
                        key="incident_id",
                        match=models.MatchValue(value=exclude_incident_id)
                    )
                )
            
            query_filter = models.Filter(
                must=filter_conditions,
                must_not=must_not if must_not else None
            )
            
            results, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=query_filter,
                limit=limit,
                with_payload=True
            )
            
            normalized = []
            for point in results:
                normalized.append({
                    "id": point.id,
                    "score": 1.0,
                    "payload": point.payload or {},
                    "source": "geo_similarity"
                })
            
            print(f"    ✓ Found {len(normalized)} disasters within ~{radius_km}km (lat/lon range)")
            return normalized
            
        except Exception as e:
            print(f"    ⚠ Geo fallback also failed: {e}")
            return []
