import os
import json
import requests
from datetime import datetime
from pathlib import Path

class SatelliteAgent:
    """Agent 1: Image Ingestion - Downloads or accesses satellite imagery (local or remote)"""
    
    def __init__(self):
        self.supported_sensors = ["Maxar", "Planet", "Sentinel-2", "WORLDVIEW03_VNIR"]
        self.imagery_cache = {}
        self.local_mode = True  # Toggle for xBD dataset vs. API downloads
    
    def fetch_esri_satellite_image(self, lat, lon, zoom=18):
        """
        Fetches an aerial image from Esri World Imagery (XYZ Tiles).
        Downloads a 2x2 grid of tiles (512x512) centered on the coordinates.
        This is a free alternative to Google Maps API.
        """
        try:
            import math
            from PIL import Image
            from io import BytesIO

            # Output path
            file_name = f"sat_{lat}_{lon}.png"
            output_dir = Path("imagery")
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / file_name
            
            if output_path.exists():
                print(f"  ✓ Using cached Esri image: {output_path}")
                return str(output_path)

            print(f"  ⬇ Fetching Esri World Imagery (Zoom {zoom})...")

            # Mercator Projection Logic
            n = 2 ** zoom
            lat_rad = math.radians(lat)
            x_val = n * ((lon + 180.0) / 360.0)
            y_val = n * (1.0 - (math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi)) / 2.0
            
            # Center logic: Get 2x2 grid around the point
            x_main = int(x_val - 0.5)
            y_main = int(y_val - 0.5)
            
            # Create blank 512x512 image
            full_image = Image.new('RGB', (512, 512))
            
            tiles_downloaded = 0
            
            # Loop 2x2 grid
            for i in range(2):
                for j in range(2):
                    tile_x = x_main + i
                    tile_y = y_main + j
                    
                    url = f"https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{zoom}/{tile_y}/{tile_x}"
                    
                    headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProjectRakshak/1.0"
                    }
                    
                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        tile = Image.open(BytesIO(response.content))
                        full_image.paste(tile, (i * 256, j * 256))
                        tiles_downloaded += 1
            
            if tiles_downloaded == 4:
                full_image.save(output_path)
                print(f"  ✓ Image saved to: {output_path} (Stitched 4 tiles)")
                return str(output_path)
            else:
                print(f"  ⚠ Failed to download all tiles ({tiles_downloaded}/4).")
                return None
                
        except Exception as e:
            print(f"  ❌ Esri Fetch Error: {e}")
            return None

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