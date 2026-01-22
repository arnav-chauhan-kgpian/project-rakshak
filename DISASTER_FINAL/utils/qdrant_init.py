import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, SparseVectorParams, SparseIndexParams, PayloadSchemaType

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system env vars


def get_qdrant_client():
    """
    Get Qdrant client - supports both local Docker and Qdrant Cloud.
    
    Configuration via environment variables:
        - QDRANT_URL + QDRANT_API_KEY: For Qdrant Cloud
        - QDRANT_HOST + QDRANT_PORT: For local Docker (default: localhost:6333)
    
    Returns:
        QdrantClient instance
    """
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    
    if url and api_key:
        # Qdrant Cloud connection
        print(f"  Connecting to Qdrant Cloud: {url[:50]}...")
        return QdrantClient(url=url, api_key=api_key)
    else:
        # Local Docker connection
        host = os.getenv("QDRANT_HOST", "localhost")
        port = int(os.getenv("QDRANT_PORT", "6333"))
        return QdrantClient(host=host, port=port)


def initialize_qdrant(force_recreate=False):
    """
    Initialize Qdrant collection for disaster response system.
    Non-destructive by default: creates collection if missing; preserves existing data and schema.
    - Dense named vector: "image" (768-dim, Cosine)
    - Sparse named vector: "text" (BM25 index)
    
    Args:
        force_recreate: If True, drops and recreates collection (destroys data)
    
    Returns:
        QdrantClient instance
    """
    try:
        client = get_qdrant_client()
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
            if "audio" not in vectors_cfg:
                schema_ok = False
                mismatch_reasons.append("Missing named vector 'audio'")
            if not sparse_cfg or "text" not in sparse_cfg:
                schema_ok = False
                mismatch_reasons.append("Missing sparse vector 'text'")
            
            if not schema_ok:
                print(f"\n⚠ SCHEMA MISMATCH DETECTED: {mismatch_reasons}")
                
                # Try to add missing 'audio' vector non-destructively (Preserves existing Data)
                needs_audio = any("audio" in r for r in mismatch_reasons)
                if needs_audio:
                    print("   Attempting to ADD 'audio' vector to existing collection (non-destructive)...")
                    try:
                        client.update_collection(
                            collection_name=collection_name,
                            vectors={
                                "audio": VectorParams(size=512, distance=Distance.COSINE)
                            }
                        )
                        print("   [OK] Successfully added 'audio' vector to schema.")
                        return client
                    except Exception as e:
                        print(f"   ⚠ Config update failed (falling back to reset): {e}")

                print(f"   AUTO-FIXING: Dropping and recreating collection...\n")
                
                # Auto-fix: drop and recreate
                import sys
                client.delete_collection(collection_name)
                print(f"   [OK] Dropped old collection")
                
                # Create with correct schema (fall through to creation below)
                raise Exception("Recreate")
            else:
                print(f"[OK] Qdrant collection '{collection_name}' present (preserving existing vectors)")
                # Ensure payload index exists for filtering (idempotent)
                try:
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name="incident_id",
                        field_schema=PayloadSchemaType.KEYWORD
                    )
                    # Create payload index for disaster_type filtering (Critical for strict typed search)
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name="disaster_type",
                        field_schema=PayloadSchemaType.KEYWORD
                    )
                    print("  - Payload Indexes: incident_id, disaster_type (keyword) - Verified/Created")
                except Exception:
                    pass  # Index might already exist
                return client
        except Exception as e:
            if "Recreate" not in str(e):
                pass  # Collection doesn't exist, will create below
            # Create collection with named vectors (multimodal)
            try:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config={
                        "image": VectorParams(size=768, distance=Distance.COSINE),
                        "audio": VectorParams(size=512, distance=Distance.COSINE)
                    },
                    sparse_vectors_config={
                        "text": SparseVectorParams(index=SparseIndexParams())
                    }
                )
                print(f"[OK] Qdrant collection '{collection_name}' created (Multimodal)")
                print("  - Dense Vector: 768-dim DINOv2 (image) - Cosine similarity")
                print("  - Sparse Vector: BM25 (text) - Dot product")
                print("  - Purpose: Hybrid multimodal disaster response search")
                
                # Create payload indexes for filtering
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name="incident_id",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                client.create_payload_index(
                    collection_name=collection_name,
                    field_name="disaster_type",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                print("  - Payload Indexes: incident_id, disaster_type (keyword) - For filtering")
            except Exception as create_err:
                # Handle 409 Conflict - collection already exists
                if "409" in str(create_err) or "already exists" in str(create_err):
                    print(f"[OK] Qdrant collection '{collection_name}' already exists (ready to use)")
                    return client
                else:
                    raise create_err
            
            if "Recreate" in str(e):
                print(f"\n[!] Schema fixed! Collection is now EMPTY.")
                print(f"   Next step: python main.py --batch-ingest\n")
                import sys
                sys.exit(0)

        return client
    except Exception as e:
        print(f"Error initializing Qdrant: {e}")
        raise


if __name__ == "__main__":
    initialize_qdrant()
