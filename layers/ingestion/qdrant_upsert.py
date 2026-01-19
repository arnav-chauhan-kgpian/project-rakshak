from qdrant_client.models import PointStruct
from datetime import datetime
from uuid import uuid5, NAMESPACE_DNS

def _safe_get(dct, *path):
    cur = dct
    for key in path:
        if cur is None:
            return None
        # Support both object-like (pydantic) and dict
        if hasattr(cur, key):
            cur = getattr(cur, key)
        elif isinstance(cur, dict):
            cur = cur.get(key)
        else:
            return None
    return cur

class QdrantUpsertAgent:
    """Agent 4: Memory Upsert - Stores multimodal embeddings and metadata in Qdrant"""
    
    def __init__(self, qdrant_client):
        self.client = qdrant_client
        self.collection_name = "disaster_memory"
        self.counter = 0
        # Detect existing collection schema to align upserts
        self.named_dense = False
        self.dense_names = []
        self.has_sparse_text = False
        try:
            info = self.client.get_collection(self.collection_name)
            # Convert to dict-like for robust inspection
            config = getattr(info, 'config', None)
            params = _safe_get(info, 'config', 'params') or getattr(config, 'params', None)

            # Detect dense vector configuration
            vectors_cfg = _safe_get(params, 'vectors')
            # In qdrant, single-vector collections may store VectorParams directly; named vectors use dict
            if isinstance(vectors_cfg, dict):
                self.named_dense = True
                self.dense_names = list(vectors_cfg.keys())
            else:
                # No named dense vectors
                self.named_dense = False
                self.dense_names = []

            # Detect sparse vectors configuration
            sparse_cfg = _safe_get(params, 'sparse_vectors')
            if isinstance(sparse_cfg, dict) and 'text' in sparse_cfg:
                self.has_sparse_text = True
        except Exception:
            # If inspection fails, default to conservative behavior (unnamed dense, no sparse)
            self.named_dense = False
            self.dense_names = []
            self.has_sparse_text = False
    
    def upsert_to_memory(self, embedding, metadata, incident_id, sparse_vector=None):
        """
        Stores multimodal embeddings (dense + optional sparse) and metadata in Qdrant.
        Uses named vectors consistent with the collection schema.
        
        Args:
            embedding: Dense vector embedding (768-dimensional DINOv2)
            metadata: Structured metadata dictionary
            incident_id: Unique identifier for this incident
            sparse_vector: Sparse vector (BM25 text embedding) - optional
            
        Returns:
            Boolean indicating success
        """
        try:
            # Use stable point IDs to avoid duplicates on re-ingest
            # Prefer incident_id as the Qdrant point ID
            
            # Prepare payload with all metadata
            payload = {
                "incident_id": incident_id,
                "disaster_type": metadata.get("disaster_type"),
                "timestamp": metadata.get("timestamp") or datetime.utcnow().isoformat(),
                "latitude": (metadata.get("geolocation", {}).get("lat_min", 0) + 
                            metadata.get("geolocation", {}).get("lat_max", 0)) / 2,
                "longitude": (metadata.get("geolocation", {}).get("lon_min", 0) + 
                             metadata.get("geolocation", {}).get("lon_max", 0)) / 2,
                "damage_severity": metadata.get("damage_severity", "unknown"),
                "damage_counts": metadata.get("damage_counts", {}),
                "confidence_score": metadata.get("confidence_score", 0.0),
                "full_metadata": metadata
            }
            
            # Prepare vectors according to detected schema
            if self.named_dense and ("image" in self.dense_names):
                vectors = {"image": embedding}
            else:
                # Unnamed single dense vector collection
                vectors = embedding

            # Attach sparse vector only if collection supports named sparse 'text'
            if self.has_sparse_text and sparse_vector is not None:
                # If dense is unnamed, Qdrant expects dict only when there are named vectors;
                # in that case, we cannot mix. So convert to dict only when dense is named.
                if isinstance(vectors, dict):
                    vectors["text"] = sparse_vector
                else:
                    # Collection doesn't support named vectors; store sparse info in payload for future use
                    payload["sparse_text"] = {
                        "indices": getattr(sparse_vector, 'indices', []),
                        "values": getattr(sparse_vector, 'values', [])
                    }
            
            # Create point with named vectors and payload
            # Use a deterministic UUID derived from incident_id (valid type for Qdrant)
            point_uuid = uuid5(NAMESPACE_DNS, str(incident_id))

            point = PointStruct(
                id=point_uuid,
                vector=vectors,
                payload=payload
            )
            
            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            return True
        except Exception as e:
            print(f"Qdrant Upsert Error: {e}")
            return False