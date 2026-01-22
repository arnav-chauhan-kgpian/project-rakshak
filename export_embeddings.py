"""
Export/Import Utility for Qdrant Embeddings.

Allows sharing pre-computed embeddings without re-running ingestion.
Supports all collections: disaster_response, memory_knowledge, memory_context, memory_history
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.http import models
import os
from dotenv import load_dotenv

load_dotenv()


def get_client():
    """Get Qdrant client from environment."""
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    
    if url and api_key:
        print(f"Connecting to Qdrant Cloud: {url}")
        return QdrantClient(url=url, api_key=api_key)
    else:
        print("Connecting to local Qdrant: localhost:6333")
        return QdrantClient(host="localhost", port=6333)


def export_collection(client: QdrantClient, collection_name: str, output_dir: Path):
    """Export a single collection to JSON."""
    try:
        # Check if collection exists
        collections = [c.name for c in client.get_collections().collections]
        if collection_name not in collections:
            print(f"  ⚠ Collection '{collection_name}' not found, skipping")
            return 0
        
        # Get collection info
        info = client.get_collection(collection_name)
        print(f"  Exporting {info.points_count} points from '{collection_name}'...")
        
        # Scroll through all points
        all_points = []
        offset = None
        batch_size = 100
        
        while True:
            points, next_offset = client.scroll(
                collection_name=collection_name,
                limit=batch_size,
                offset=offset,
                with_vectors=True,
                with_payload=True
            )
            
            for point in points:
                # Handle both named and unnamed vectors
                if isinstance(point.vector, dict):
                    vector_data = {k: v for k, v in point.vector.items()}
                else:
                    vector_data = point.vector
                
                all_points.append({
                    "id": str(point.id),
                    "vector": vector_data,
                    "payload": point.payload
                })
            
            if next_offset is None:
                break
            offset = next_offset
        
        # Save to file
        output_file = output_dir / f"{collection_name}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({
                "collection_name": collection_name,
                "points_count": len(all_points),
                "exported_at": datetime.now().isoformat(),
                "points": all_points
            }, f, indent=2)
        
        print(f"  ✓ Saved {len(all_points)} points to {output_file}")
        return len(all_points)
        
    except Exception as e:
        print(f"  ✗ Error exporting {collection_name}: {e}")
        return 0


def import_collection(client: QdrantClient, input_file: Path, recreate: bool = False):
    """Import a collection from JSON."""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        collection_name = data["collection_name"]
        points = data["points"]
        print(f"  Importing {len(points)} points to '{collection_name}'...")
        
        # Check if collection exists
        collections = [c.name for c in client.get_collections().collections]
        
        if collection_name in collections:
            if recreate:
                print(f"  Recreating collection '{collection_name}'...")
                client.delete_collection(collection_name)
            else:
                print(f"  Collection exists, adding points...")
        
        # Detect vector config from first point
        first_vector = points[0]["vector"] if points else {}
        
        if collection_name not in [c.name for c in client.get_collections().collections]:
            # Create collection with appropriate config
            if isinstance(first_vector, dict):
                # Named vectors
                vectors_config = {}
                for name, vec in first_vector.items():
                    if name == "sparse":
                        continue  # Handle sparse separately
                    vectors_config[name] = models.VectorParams(
                        size=len(vec),
                        distance=models.Distance.COSINE
                    )
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=vectors_config
                )
            else:
                # Single vector
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=len(first_vector),
                        distance=models.Distance.COSINE
                    )
                )
        
        # Batch upsert points
        batch_size = 100
        for i in range(0, len(points), batch_size):
            batch = points[i:i+batch_size]
            qdrant_points = []
            
            for p in batch:
                qdrant_points.append(models.PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p["payload"]
                ))
            
            client.upsert(collection_name=collection_name, points=qdrant_points)
        
        print(f"  ✓ Imported {len(points)} points to '{collection_name}'")
        return len(points)
        
    except Exception as e:
        print(f"  ✗ Error importing {input_file}: {e}")
        return 0


def export_all(output_dir: str = "exports"):
    """Export all collections to a directory."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"\n=== Exporting Qdrant Collections ===")
    print(f"Output directory: {output_path.absolute()}\n")
    
    client = get_client()
    
    collections = [
        "disaster_memory",      # Main incident embeddings
        "disaster_knowledge",   # Learned patterns
        "disaster_context",     # Session context
        "disaster_history"      # Interaction logs
    ]
    
    total = 0
    for collection in collections:
        total += export_collection(client, collection, output_path)
    
    print(f"\n=== Export Complete ===")
    print(f"Total points exported: {total}")
    print(f"Share the '{output_dir}' folder with your friend!")


def import_all(input_dir: str = "exports", recreate: bool = False):
    """Import all collections from a directory."""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"Error: Directory '{input_dir}' not found")
        return
    
    print(f"\n=== Importing Qdrant Collections ===")
    print(f"Input directory: {input_path.absolute()}\n")
    
    client = get_client()
    
    json_files = list(input_path.glob("*.json"))
    if not json_files:
        print("No JSON files found to import")
        return
    
    total = 0
    for json_file in json_files:
        total += import_collection(client, json_file, recreate)
    
    print(f"\n=== Import Complete ===")
    print(f"Total points imported: {total}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export/Import Qdrant embeddings")
    parser.add_argument("action", choices=["export", "import"], help="Action to perform")
    parser.add_argument("--dir", default="exports", help="Directory for export/import (default: exports)")
    parser.add_argument("--recreate", action="store_true", help="Recreate collections on import")
    
    args = parser.parse_args()
    
    if args.action == "export":
        export_all(args.dir)
    else:
        import_all(args.dir, args.recreate)
