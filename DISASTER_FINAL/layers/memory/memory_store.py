"""
Long-Term Memory Store with Qdrant Integration.

Provides three memory layers:
- Knowledge: Permanent facts and learned patterns (no decay)
- Context: Session-based context (24h TTL, decay)
- History: Interaction logs (30d TTL, decay)

Supports evolving representations: updates, deletions, decay, and reinforcement.
"""

import math
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Literal

from qdrant_client import models


MemoryType = Literal["knowledge", "context", "history"]


class MemoryStore:
    """
    Unified memory store with three layers backed by Qdrant.
    
    Memory Lifecycle:
        Created → Active → Decaying → Archived → Deleted
        
    Access reinforcement bumps importance score.
    Time-based exponential decay reduces old memories.
    """
    
    # Collection configuration
    COLLECTIONS = {
        "knowledge": {
            "name": "disaster_knowledge",
            "ttl_days": None,  # Permanent
            "decay_half_life_days": None,  # No decay
        },
        "context": {
            "name": "disaster_context",
            "ttl_days": 1,  # 24 hours
            "decay_half_life_days": 0.5,  # Rapid decay
        },
        "history": {
            "name": "disaster_history",
            "ttl_days": 30,  # 30 days
            "decay_half_life_days": 7,  # Week-based decay
        }
    }
    
    # Vector dimensions (matching existing embeddings)
    VECTOR_DIM = 768  # DINOv2 embeddings
    
    def __init__(self, qdrant_client):
        """Initialize memory store with Qdrant client."""
        self.client = qdrant_client
        self._ensure_collections_exist()
    
    def _ensure_collections_exist(self):
        """Create memory collections if they don't exist."""
        for memory_type, config in self.COLLECTIONS.items():
            collection_name = config["name"]
            try:
                self.client.get_collection(collection_name)
            except Exception:
                # Collection doesn't exist, create it
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=self.VECTOR_DIM,
                        distance=models.Distance.COSINE
                    )
                )
                # Create payload indexes for efficient filtering
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="created_at",
                    field_schema=models.PayloadSchemaType.DATETIME
                )
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="last_accessed",
                    field_schema=models.PayloadSchemaType.DATETIME
                )
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name="memory_type",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                print(f"  ✓ Created memory collection: {collection_name}")
    
    # ==================== CRUD Operations ====================
    
    def store(
        self,
        memory_type: MemoryType,
        content: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        importance_score: float = 0.5,
        session_id: Optional[str] = None,
        source_incident_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Store a new memory.
        
        Args:
            memory_type: "knowledge", "context", or "history"
            content: Text content of the memory
            embedding: Vector embedding (768-dim)
            metadata: Additional metadata dict
            importance_score: Base importance (0-1)
            session_id: Session identifier (for context)
            source_incident_id: Related incident ID
            tags: List of tags for categorization
            
        Returns:
            Memory ID (UUID string)
        """
        config = self.COLLECTIONS.get(memory_type)
        if not config:
            raise ValueError(f"Invalid memory type: {memory_type}")
        
        memory_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat() + "Z"
        
        payload = {
            "memory_type": memory_type,
            "content": content,
            "created_at": now,
            "last_accessed": now,
            "access_count": 1,
            "importance_score": importance_score,
            "decay_half_life_days": config["decay_half_life_days"],
            "session_id": session_id,
            "source_incident_id": source_incident_id,
            "tags": tags or [],
            "status": "active",  # active, decaying, archived
            **(metadata or {})
        }
        
        self.client.upsert(
            collection_name=config["name"],
            points=[
                models.PointStruct(
                    id=memory_id,
                    vector=embedding,
                    payload=payload
                )
            ]
        )
        
        return memory_id
    
    def retrieve(
        self,
        query_embedding: List[float],
        memory_type: MemoryType,
        limit: int = 10,
        min_score: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
        apply_decay: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories similar to query embedding.
        
        Args:
            query_embedding: Query vector (768-dim)
            memory_type: Which memory layer to search
            limit: Maximum results
            min_score: Minimum similarity threshold
            filters: Additional payload filters
            apply_decay: Whether to apply decay scoring
            
        Returns:
            List of memory dicts with scores
        """
        config = self.COLLECTIONS.get(memory_type)
        if not config:
            raise ValueError(f"Invalid memory type: {memory_type}")
        
        # Build filter conditions
        filter_conditions = []
        if filters:
            for key, value in filters.items():
                filter_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value)
                    )
                )
        
        query_filter = None
        if filter_conditions:
            query_filter = models.Filter(must=filter_conditions)
        
        # Execute search
        results = self.client.search(
            collection_name=config["name"],
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=limit,
            score_threshold=min_score,
            with_payload=True
        )
        
        # Process results with decay scoring
        memories = []
        for result in results:
            memory = {
                "id": result.id,
                "score": result.score,
                "payload": result.payload
            }
            
            # Apply decay if enabled
            if apply_decay and config["decay_half_life_days"]:
                effective_score = self._calculate_effective_score(result.payload)
                memory["effective_score"] = effective_score
                memory["decay_factor"] = effective_score / max(result.payload.get("importance_score", 0.5), 0.01)
            else:
                memory["effective_score"] = result.score
                memory["decay_factor"] = 1.0
            
            memories.append(memory)
            
            # Reinforce on access (async-safe)
            self._increment_access(config["name"], result.id)
        
        # Sort by effective score
        memories.sort(key=lambda x: x["effective_score"], reverse=True)
        return memories
    
    def update(
        self,
        memory_id: str,
        memory_type: MemoryType,
        payload_updates: Dict[str, Any]
    ) -> bool:
        """
        Update memory payload fields.
        
        Args:
            memory_id: UUID of the memory
            memory_type: Which layer the memory is in
            payload_updates: Dict of fields to update
            
        Returns:
            Success boolean
        """
        config = self.COLLECTIONS.get(memory_type)
        if not config:
            return False
        
        try:
            self.client.set_payload(
                collection_name=config["name"],
                payload=payload_updates,
                points=[memory_id]
            )
            return True
        except Exception as e:
            print(f"Memory update error: {e}")
            return False
    
    def delete(
        self,
        memory_id: str,
        memory_type: MemoryType
    ) -> bool:
        """
        Delete a memory.
        
        Args:
            memory_id: UUID of the memory
            memory_type: Which layer the memory is in
            
        Returns:
            Success boolean
        """
        config = self.COLLECTIONS.get(memory_type)
        if not config:
            return False
        
        try:
            self.client.delete(
                collection_name=config["name"],
                points_selector=models.PointIdsList(points=[memory_id])
            )
            return True
        except Exception as e:
            print(f"Memory delete error: {e}")
            return False
    
    # ==================== Lifecycle Operations ====================
    
    def reinforce(self, memory_id: str, memory_type: MemoryType) -> bool:
        """
        Reinforce a memory (bump access count and timestamp).
        
        Args:
            memory_id: UUID of the memory
            memory_type: Which layer
            
        Returns:
            Success boolean
        """
        config = self.COLLECTIONS.get(memory_type)
        if not config:
            return False
        
        try:
            # Get current access count
            points = self.client.retrieve(
                collection_name=config["name"],
                ids=[memory_id],
                with_payload=True
            )
            
            if not points:
                return False
            
            current_count = points[0].payload.get("access_count", 0)
            now = datetime.utcnow().isoformat() + "Z"
            
            self.client.set_payload(
                collection_name=config["name"],
                payload={
                    "access_count": current_count + 1,
                    "last_accessed": now,
                    "status": "active"  # Reactivate if decaying
                },
                points=[memory_id]
            )
            return True
        except Exception as e:
            print(f"Memory reinforce error: {e}")
            return False
    
    def apply_decay_batch(self, memory_type: MemoryType) -> int:
        """
        Apply decay scoring to all memories in a layer.
        Updates status to 'decaying' or 'archived' based on effective score.
        
        Args:
            memory_type: Which layer to process
            
        Returns:
            Number of memories updated
        """
        config = self.COLLECTIONS.get(memory_type)
        if not config or not config["decay_half_life_days"]:
            return 0  # No decay for this layer
        
        updated_count = 0
        offset = None
        
        try:
            while True:
                # Scroll through all points
                scroll_result = self.client.scroll(
                    collection_name=config["name"],
                    limit=100,
                    offset=offset,
                    with_payload=True
                )
                
                points, offset = scroll_result
                if not points:
                    break
                
                for point in points:
                    effective_score = self._calculate_effective_score(point.payload)
                    
                    # Determine status based on effective score
                    if effective_score < 0.1:
                        new_status = "archived"
                    elif effective_score < 0.3:
                        new_status = "decaying"
                    else:
                        new_status = "active"
                    
                    # Update if status changed
                    current_status = point.payload.get("status", "active")
                    if new_status != current_status:
                        self.client.set_payload(
                            collection_name=config["name"],
                            payload={"status": new_status},
                            points=[point.id]
                        )
                        updated_count += 1
                
                if offset is None:
                    break
                    
        except Exception as e:
            print(f"Decay batch error: {e}")
        
        return updated_count
    
    def cleanup_expired(self, memory_type: MemoryType) -> int:
        """
        Delete memories that have exceeded their TTL.
        
        Args:
            memory_type: Which layer to clean
            
        Returns:
            Number of memories deleted
        """
        config = self.COLLECTIONS.get(memory_type)
        if not config or not config["ttl_days"]:
            return 0  # No TTL for this layer
        
        try:
            cutoff = datetime.utcnow() - timedelta(days=config["ttl_days"])
            cutoff_str = cutoff.isoformat() + "Z"
            
            # Delete using filter
            self.client.delete(
                collection_name=config["name"],
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="created_at",
                                range=models.DatetimeRange(lt=cutoff_str)
                            )
                        ]
                    )
                )
            )
            
            # Return estimated count (Qdrant doesn't return delete count)
            return -1  # Unknown count
        except Exception as e:
            print(f"Cleanup error: {e}")
            return 0
    
    # ==================== Memory Queries ====================
    
    def get_recent_context(
        self,
        session_id: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get recent context memories for a session."""
        config = self.COLLECTIONS["context"]
        
        try:
            results = self.client.scroll(
                collection_name=config["name"],
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="session_id",
                            match=models.MatchValue(value=session_id)
                        )
                    ]
                ),
                limit=limit,
                with_payload=True,
                order_by=models.OrderBy(
                    key="created_at",
                    direction=models.Direction.DESC
                )
            )
            
            return [{"id": p.id, "payload": p.payload} for p in results[0]]
        except Exception as e:
            print(f"Get context error: {e}")
            return []
    
    def get_knowledge_by_tags(
        self,
        tags: List[str],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get knowledge memories matching any of the given tags."""
        config = self.COLLECTIONS["knowledge"]
        
        try:
            results = self.client.scroll(
                collection_name=config["name"],
                scroll_filter=models.Filter(
                    should=[
                        models.FieldCondition(
                            key="tags",
                            match=models.MatchValue(value=tag)
                        )
                        for tag in tags
                    ]
                ),
                limit=limit,
                with_payload=True
            )
            
            return [{"id": p.id, "payload": p.payload} for p in results[0]]
        except Exception as e:
            print(f"Get knowledge error: {e}")
            return []
    
    def get_incident_history(
        self,
        incident_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get history memories for a specific incident."""
        config = self.COLLECTIONS["history"]
        
        try:
            results = self.client.scroll(
                collection_name=config["name"],
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="source_incident_id",
                            match=models.MatchValue(value=incident_id)
                        )
                    ]
                ),
                limit=limit,
                with_payload=True
            )
            
            return [{"id": p.id, "payload": p.payload} for p in results[0]]
        except Exception as e:
            print(f"Get history error: {e}")
            return []
    
    # ==================== Internal Helpers ====================
    
    def _calculate_effective_score(self, payload: Dict[str, Any]) -> float:
        """
        Calculate effective score with time decay and access reinforcement.
        
        Formula:
            effective = base_score * (1 + access_bonus) * decay_factor
            
        Where:
            access_bonus = min(1.0, log(access_count + 1) / 3)  # Caps at 2x
            decay_factor = exp(-0.693 * days_since_access / half_life)
        """
        base_score = payload.get("importance_score", 0.5)
        access_count = payload.get("access_count", 1)
        half_life = payload.get("decay_half_life_days")
        
        # Access reinforcement (logarithmic, caps at 2x)
        access_bonus = min(1.0, math.log(access_count + 1) / 3)
        
        # Time decay
        decay_factor = 1.0
        if half_life:
            last_accessed_str = payload.get("last_accessed", "")
            if last_accessed_str:
                try:
                    last_accessed = datetime.fromisoformat(last_accessed_str.replace("Z", "+00:00"))
                    days_since = (datetime.utcnow().replace(tzinfo=last_accessed.tzinfo) - last_accessed).days
                    decay_factor = math.exp(-0.693 * days_since / half_life)
                except:
                    pass
        
        return base_score * (1 + access_bonus) * decay_factor
    
    def _increment_access(self, collection_name: str, memory_id: str):
        """Increment access count (fire-and-forget helper)."""
        try:
            now = datetime.utcnow().isoformat() + "Z"
            points = self.client.retrieve(
                collection_name=collection_name,
                ids=[memory_id],
                with_payload=["access_count"]
            )
            if points:
                current = points[0].payload.get("access_count", 0)
                self.client.set_payload(
                    collection_name=collection_name,
                    payload={
                        "access_count": current + 1,
                        "last_accessed": now
                    },
                    points=[memory_id],
                    wait=False  # Async
                )
        except:
            pass  # Silent fail for access tracking
    
    # ==================== Stats ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics for all layers."""
        stats = {}
        for memory_type, config in self.COLLECTIONS.items():
            try:
                info = self.client.get_collection(config["name"])
                stats[memory_type] = {
                    "collection": config["name"],
                    "point_count": info.points_count,
                    "ttl_days": config["ttl_days"],
                    "decay_half_life_days": config["decay_half_life_days"]
                }
            except Exception as e:
                stats[memory_type] = {"error": str(e)}
        return stats
