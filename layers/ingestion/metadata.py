import json
import re
from datetime import datetime
from pathlib import Path

class MetadataAgent:
    """Agent 3: JSON Parsing - Extracts and structures metadata from satellite data"""
    
    def __init__(self):
        self.schema_version = "1.0"
    
    def parse_metadata(self, image_path, aoi_bounds=None, disaster_type=None):
        """
        Parses and structures metadata from xBD JSON label files.
        
        Args:
            image_path: Path to satellite image
            aoi_bounds: Area of interest boundaries (optional, computed from JSON)
            disaster_type: Type of disaster (optional, extracted from JSON)
            
        Returns:
            Structured metadata dictionary with damage assessment
        """
        try:
            # Find corresponding JSON label file
            img_path = Path(image_path)
            label_path = img_path.parent.parent / "labels" / (img_path.stem + ".json")
            
            if not label_path.exists():
                # Fallback to mock metadata
                return self._create_mock_metadata(image_path, aoi_bounds, disaster_type)
            
            # Parse JSON label file
            with open(label_path, 'r') as f:
                data = json.load(f)
            
            metadata_raw = data.get("metadata", {})
            features = data.get("features", {}).get("lng_lat", [])
            
            # Extract disaster type from filename or metadata
            disaster_name = metadata_raw.get("disaster", "")
            disaster_type_parsed = metadata_raw.get("disaster_type", disaster_type)
            
            # Map disaster types to standard format
            disaster_type_map = {
                "volcano": "volcano",
                "flooding": "flood",
                "earthquake": "earthquake",
                "wildfire": "wildfire",
                "tsunami": "tsunami",
                "fire": "wildfire"
            }
            
            # Extract disaster type from disaster name if needed
            for key, value in disaster_type_map.items():
                if key in disaster_name.lower() or (disaster_type_parsed and key in disaster_type_parsed.lower()):
                    disaster_type = value
                    break
            
            # Handle hurricane as a separate type
            if "hurricane" in disaster_name.lower():
                disaster_type = "hurricane"
            
            # Calculate damage severity from building features
            damage_counts = {
                "no-damage": 0,
                "minor-damage": 0,
                "major-damage": 0,
                "destroyed": 0
            }
            
            for feature in features:
                subtype = feature.get("properties", {}).get("subtype", "")
                if subtype in damage_counts:
                    damage_counts[subtype] += 1
            
            # Determine overall severity
            total_buildings = sum(damage_counts.values())
            if total_buildings > 0:
                destroyed_ratio = damage_counts["destroyed"] / total_buildings
                major_ratio = damage_counts["major-damage"] / total_buildings
                
                if destroyed_ratio > 0.3:
                    severity = "critical"
                elif destroyed_ratio > 0.1 or major_ratio > 0.3:
                    severity = "high"
                elif damage_counts["minor-damage"] + damage_counts["major-damage"] > 0:
                    severity = "medium"
                else:
                    severity = "low"
            else:
                severity = "unknown"
            
            # Extract geographic bounds
            if features and "wkt" in features[0]:
                # Parse WKT polygon to extract lat/lon bounds
                lats,lons = [], []
                for feature in features:
                    wkt = feature.get("wkt", "")
                    # Extract coordinates from WKT POLYGON format
                    coords = re.findall(r"([-\d.]+)\s+([-\d.]+)", wkt)
                    for lon, lat in coords:
                        lons.append(float(lon))
                        lats.append(float(lat))
                
                if lats and lons:
                    aoi_bounds = {
                        "lat_min": min(lats),
                        "lat_max": max(lats),
                        "lon_min": min(lons),
                        "lon_max": max(lons)
                    }
            
            # Build structured metadata
            metadata = {
                "schema_version": self.schema_version,
                "timestamp": datetime.now().isoformat(),
                "image_path": str(image_path),
                "disaster_type": disaster_type or "unknown",
                "disaster_name": disaster_name,
                "damage_severity": severity,
                "damage_counts": damage_counts,
                "total_buildings": total_buildings,
                "geolocation": aoi_bounds or {
                    "lat_min": 0, "lat_max": 0, "lon_min": 0, "lon_max": 0
                },
                "acquisition_date": metadata_raw.get("capture_date", datetime.now().isoformat()),
                "sensor_info": {
                    "type": metadata_raw.get("sensor", "WORLDVIEW03_VNIR"),
                    "provider": metadata_raw.get("provider_asset_type", "Unknown"),
                    "gsd": metadata_raw.get("gsd", 1.0),
                    "resolution": metadata_raw.get("pan_resolution", 0.3)
                },
                "quality_metrics": {
                    "off_nadir_angle": metadata_raw.get("off_nadir_angle", 0),
                    "sun_azimuth": metadata_raw.get("sun_azimuth", 0),
                    "sun_elevation": metadata_raw.get("sun_elevation", 0)
                },
                "image_dimensions": {
                    "width": metadata_raw.get("width", 1024),
                    "height": metadata_raw.get("height", 1024)
                },
                "catalog_id": metadata_raw.get("catalog_id", "")
            }
            
            return metadata
            
        except Exception as e:
            print(f"Metadata Agent Error: {e}")
            return self._create_mock_metadata(image_path, aoi_bounds, disaster_type)
    
    def _create_mock_metadata(self, image_path, aoi_bounds, disaster_type):
        """Create mock metadata when JSON file is not available"""
        return {
            "schema_version": self.schema_version,
            "timestamp": datetime.now().isoformat(),
            "image_path": str(image_path),
            "disaster_type": disaster_type or "unknown",
            "damage_severity": "medium",
            "damage_counts": {"no-damage": 0, "minor-damage": 0, "major-damage": 0, "destroyed": 0},
            "total_buildings": 0,
            "geolocation": aoi_bounds or {"lat_min": 0, "lat_max": 0, "lon_min": 0, "lon_max": 0},
            "acquisition_date": datetime.now().isoformat(),
            "sensor_info": {"type": "Multispectral", "bands": 4, "resolution_cm": 15},
            "quality_metrics": {"cloud_cover_percent": 5.2, "atmospheric_opacity": 0.08, "signal_to_noise_ratio": 45.3}
        }