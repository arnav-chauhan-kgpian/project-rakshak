"""Diagnostic script to check Qdrant collection state"""
from qdrant_client import QdrantClient

def diagnose_collection():
    try:
        client = QdrantClient("localhost", port=6333)
        collection_name = "disaster_memory"
        
        print("="*70)
        print("QDRANT COLLECTION DIAGNOSTIC")
        print("="*70 + "\n")
        
        # Get collection info
        try:
            info = client.get_collection(collection_name)
            print(f"✓ Collection '{collection_name}' exists\n")
            
            # Extract config
            config = info.config
            params = config.params
            
            # Vector config
            print("VECTOR CONFIGURATION:")
            vectors_cfg = params.vectors
            if isinstance(vectors_cfg, dict):
                print(f"  Named vectors: {list(vectors_cfg.keys())}")
                for name, cfg in vectors_cfg.items():
                    print(f"    - {name}: size={cfg.size}, distance={cfg.distance}")
            else:
                print(f"  Single unnamed vector: size={vectors_cfg.size}, distance={vectors_cfg.distance}")
            
            # Sparse vectors
            print("\nSPARSE VECTOR CONFIGURATION:")
            sparse_cfg = params.sparse_vectors
            if sparse_cfg:
                print(f"  Sparse vectors: {list(sparse_cfg.keys())}")
            else:
                print("  No sparse vectors configured")
            
            # Point count
            print(f"\nPOINT COUNT: {info.points_count} incidents stored")
            
            # Sample a few points to check schema
            if info.points_count > 0:
                print("\nSAMPLE POINTS (first 3):")
                scroll_result = client.scroll(
                    collection_name=collection_name,
                    limit=3,
                    with_payload=True,
                    with_vectors=False
                )
                points, _ = scroll_result
                for i, p in enumerate(points, 1):
                    payload = p.payload
                    print(f"  {i}. ID={p.id} | incident_id={payload.get('incident_id')} | "
                          f"type={payload.get('disaster_type')} | "
                          f"lat={payload.get('latitude'):.2f}, lon={payload.get('longitude'):.2f}")
            else:
                print("\n⚠ Collection is EMPTY - no incidents stored!")
                print("  → Run: python main.py --batch-ingest")
            
        except Exception as e:
            print(f"❌ Collection '{collection_name}' not found or error: {e}")
            return
        
        print("\n" + "="*70)
        print("DIAGNOSIS COMPLETE")
        print("="*70)
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_collection()
