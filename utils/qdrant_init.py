from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, SparseVectorParams, SparseIndexParams


def initialize_qdrant(force_recreate=False):
    """
    Initialize Qdrant collection for disaster response system.
    Non-destructive by default: creates collection if missing; preserves existing data and schema.
    - Dense named vector: "image" (768-dim, Cosine)
    - Sparse named vector: "text" (BM25 index)
    
    Args:
        force_recreate: If True, drops and recreates collection (destroys data)
    """
    try:
        client = QdrantClient("localhost", port=6333)

        collection_name = "disaster_memory"

        # Force recreate if requested
        if force_recreate:
            try:
                client.delete_collection(collection_name)
                print(f"⚠ Dropped existing collection '{collection_name}'")
            except Exception:
                pass

        try:
            # If collection exists, check schema compatibility
            info = client.get_collection(collection_name)
            config = info.config
            params = config.params
            vectors_cfg = params.vectors
            sparse_cfg = params.sparse_vectors
            
            # Detect schema mismatch
            schema_ok = True
            mismatch_reasons = []
            
            if not isinstance(vectors_cfg, dict) or "image" not in vectors_cfg:
                schema_ok = False
                mismatch_reasons.append("Missing named vector 'image'")
            if not sparse_cfg or "text" not in sparse_cfg:
                schema_ok = False
                mismatch_reasons.append("Missing sparse vector 'text'")
            
            if not schema_ok:
                print(f"\n⚠ SCHEMA MISMATCH DETECTED:")
                for reason in mismatch_reasons:
                    print(f"   - {reason}")
                print(f"\n   Collection has {info.points_count} points with incompatible schema.")
                print(f"   AUTO-FIXING: Dropping and recreating collection...\n")
                
                # Auto-fix: drop and recreate
                import sys
                client.delete_collection(collection_name)
                print(f"   ✓ Dropped old collection")
                
                # Create with correct schema (fall through to creation below)
                raise Exception("Recreate")
            else:
                print(f"✓ Qdrant collection '{collection_name}' present (preserving existing vectors)")
                return client
        except Exception as e:
            if "Recreate" not in str(e):
                pass  # Collection doesn't exist, will create below
            # Create collection with named vectors (multimodal)
            client.create_collection(
                collection_name=collection_name,
                vectors_config={
                    "image": VectorParams(size=768, distance=Distance.COSINE)
                },
                sparse_vectors_config={
                    "text": SparseVectorParams(index=SparseIndexParams())
                }
            )
            print(f"✓ Qdrant collection '{collection_name}' created (Multimodal)")
            print("  - Dense Vector: 768-dim DINOv2 (image) - Cosine similarity")
            print("  - Sparse Vector: BM25 (text) - Dot product")
            print("  - Purpose: Hybrid multimodal disaster response search")
            
            if "Recreate" in str(e):
                print(f"\n⚠ Schema fixed! Collection is now EMPTY.")
                print(f"   Next step: python main.py --batch-ingest\n")
                import sys
                sys.exit(0)

        return client
    except Exception as e:
        print(f"Error initializing Qdrant: {e}")
        raise

if __name__ == "__main__":
    initialize_qdrant()
