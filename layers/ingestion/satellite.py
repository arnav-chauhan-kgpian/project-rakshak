import os
import json
from datetime import datetime
from pathlib import Path

class SatelliteAgent:
    """Agent 1: Image Ingestion - Downloads or accesses satellite imagery (local or remote)"""
    
    def __init__(self):
        self.supported_sensors = ["Maxar", "Planet", "Sentinel-2", "WORLDVIEW03_VNIR"]
        self.imagery_cache = {}
        self.local_mode = True  # Toggle for xBD dataset vs. API downloads
    
    def download_imagery(self, aoi_bounds, sensor="Maxar", date_range=None):
        """
        Downloads satellite imagery for Area of Interest (AOI).
        
        Args:
            aoi_bounds: Dict with keys lat_min, lat_max, lon_min, lon_max
            sensor: Satellite sensor type (Maxar, Planet, Sentinel-2)
            date_range: Tuple of (start_date, end_date)
            
        Returns:
            List of image paths and metadata
        """
        try:
            # In production: connect to real API (Maxar, Planet Labs, etc.)
            # For now: return mock data structure
            imagery_metadata = {
                "source": sensor,
                "aoi": aoi_bounds,
                "timestamp": datetime.now().isoformat(),
                "resolution_cm": 15 if sensor == "Maxar" else 30,
                "cloud_cover": 0.05,
                "images": [
                    {
                        "path": f"imagery/tile_001_{sensor}.tif",
                        "band_count": 4 if sensor != "Sentinel-2" else 11,
                        "geotransform": {
                            "lat_min": aoi_bounds["lat_min"],
                            "lat_max": aoi_bounds["lat_max"],
                            "lon_min": aoi_bounds["lon_min"],
                            "lon_max": aoi_bounds["lon_max"]
                        }
                    }
                ]
            }
            self.imagery_cache[str(aoi_bounds)] = imagery_metadata
            return imagery_metadata["images"]
        except Exception as e:
            print(f"Satellite Agent Error: {e}")
            return []
    
    def access_local_image(self, image_path):
        """
        Accesses local xBD satellite image instead of downloading.
        
        Args:
            image_path: Path to local image file
            
        Returns:
            Image metadata dictionary
        """
        try:
            img_path = Path(image_path)
            
            if not img_path.exists():
                print(f"Warning: Image not found: {image_path}")
                return None
            
            # Extract disaster info from filename
            filename = img_path.stem
            parts = filename.split('_')
            disaster_name = parts[0] if len(parts) > 0 else "unknown"
            
            metadata = {
                "source": "xBD_local",
                "path": str(img_path),
                "filename": filename,
                "disaster": disaster_name,
                "timestamp": datetime.now().isoformat(),
                "exists": True,
                "file_size_bytes": img_path.stat().st_size
            }
            
            return metadata
        except Exception as e:
            print(f"Local Image Access Error: {e}")
            return None