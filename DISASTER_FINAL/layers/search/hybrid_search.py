"""
Agent 6: Qdrant Search Executor
Performs multimodal hybrid search using official Qdrant prefetch + RRF fusion API.

Combines:
- Dense vectors (DINOv2 image embeddings) via named vector "image"
- Sparse vectors (BM25 text) via named vector "text"
- Server-side Reciprocal Rank Fusion (RRF) for result merging
"""

from qdrant_client import models


class SearchExecutionAgent:
    """Agent 6: Qdrant Search Executor - Performs multimodal hybrid search (dense + sparse + metadata)"""
    
    def __init__(self, qdrant_client):
        self.client = qdrant_client
        self.collection_name = "disaster_memory"
    
    def execute_search(self, query_vector, latitude, longitude, plan, 
                       sparse_query_vector=None, exclude_incident_id=None):
        """
        Executes hybrid search using official Qdrant prefetch + RRF fusion.
        
        This uses Qdrant's server-side Reciprocal Rank Fusion (RRF) to combine:
        - Dense vector search on "image" (DINOv2 embeddings)
        - Sparse vector search on "text" (BM25 tokens)
        
        Args:
            query_vector: Dense query embedding (768-dimensional DINOv2)
            latitude: Center latitude for spatial search
            longitude: Center longitude for spatial search
            plan: Search plan from QueryPlannerAgent
            sparse_query_vector: Sparse query vector (SparseVector from BM25)
            exclude_incident_id: Optional incident ID to exclude from results
            
        Returns:
            List of search results with fused scores
        """
        try:
            max_results = plan.get("max_results", 10)
            prefetch_limit = max_results * 3  # Increased for better RRF fusion quality
            target_disaster_type = plan.get("disaster_filter", None)
            
            # Build filter with strict disaster type matching + ID exclusion
            must_conditions = []
            must_not_conditions = []
            
            # 1. Strict Disaster Type Filter (Critical for correct classification)
            if target_disaster_type:
                must_conditions.append(
                    models.FieldCondition(
                        key="disaster_type", 
                        match=models.MatchValue(value=target_disaster_type)
                    )
                )
            
            # 2. Exclude Incident ID
            if exclude_incident_id:
                must_not_conditions.append(
                    models.FieldCondition(
                        key="incident_id",
                        match=models.MatchValue(value=exclude_incident_id)
                    )
                )
            
            query_filter = models.Filter(
                must=must_conditions if must_conditions else None,
                must_not=must_not_conditions if must_not_conditions else None
            )
            
            # Build prefetch queries for hybrid search
            prefetch = []
            
            # Dense vector search (image embeddings)
            prefetch.append(
                models.Prefetch(
                    query=list(query_vector),
                    using="image",
                    limit=prefetch_limit,
                    filter=query_filter
                )
            )
            
            # Sparse vector search (BM25 text) - if available
            if sparse_query_vector is not None:
                try:
                    # sparse_query_vector should be a SparseVector with indices and values
                    sparse_query = models.SparseVector(
                        indices=list(sparse_query_vector.indices),
                        values=list(sparse_query_vector.values)
                    )
                    prefetch.append(
                        models.Prefetch(
                            query=sparse_query,
                            using="text",
                            limit=prefetch_limit,
                            filter=query_filter
                        )
                    )
                except Exception as sparse_err:
                    print(f"  ⚠ Sparse vector prefetch skipped: {sparse_err}")
            
            # Initialize results before try block
            results = []
            
            # Execute hybrid query with server-side RRF fusion
            try:
                response = self.client.query_points(
                    collection_name=self.collection_name,
                    prefetch=prefetch,
                    query=models.FusionQuery(fusion=models.Fusion.RRF),
                    limit=max_results,
                    with_payload=True
                )
                results = self._normalize_results(response.points, target_disaster_type)
                
                if results:
                    fusion_type = "dense+sparse" if len(prefetch) > 1 else "dense-only"
                    print(f"  ✓ Hybrid search ({fusion_type} RRF): {len(results)} results")
                    return results
                    
            except Exception as hybrid_err:
                print(f"  ⚠ Hybrid search error: {hybrid_err}")
                results = []  # Ensure results is empty list on error
            
            # Fallback: Dense-only search (no fusion)
            if len(results) == 0:
                print("  ⚠ Falling back to dense-only search...")
                try:
                    response = self.client.query_points(
                        collection_name=self.collection_name,
                        query=list(query_vector),
                        using="image",
                        query_filter=query_filter,
                        limit=max_results,
                        with_payload=True
                    )
                    results = self._normalize_results(response.points, target_disaster_type)
                    if results:
                        print(f"  ✓ Dense-only search: {len(results)} results")
                except Exception as dense_err:
                    print(f"  ✗ Dense-only search error: {dense_err}")
                    results = []
            
            # Global fallback: Search without filters if still empty
            if len(results) == 0 and plan.get("allow_global_fallback", True):
                print("  ⚠ No results with filters, trying global search...")
                try:
                    response = self.client.query_points(
                        collection_name=self.collection_name,
                        query=list(query_vector),
                        using="image",
                        limit=max_results,
                        with_payload=True
                    )
                    results = self._normalize_results(response.points, target_disaster_type)
                    if results:
                        print(f"  ✓ Global search found {len(results)} results")
                except Exception as global_err:
                    print(f"  ✗ Global search error: {global_err}")
            
            return results
            
        except Exception as e:
            print(f"Hybrid Search Error: {e}")
            return []

    def _normalize_results(self, points, target_disaster_type=None):
        """Convert Qdrant ScoredPoint objects into plain dicts with score boosting and deduplication."""
        normalized = []
        seen_incident_ids = set()  # For deduplication
        
        for idx, p in enumerate(points or []):
            try:
                # Check if p is a dict or an object with attributes
                if isinstance(p, dict):
                    payload = p.get("payload", {})
                    score = p.get("score", 0)
                    point_id = p.get("id", idx)
                else:
                    # Object-style access (ScoredPoint)
                    payload = getattr(p, "payload", {})
                    score = getattr(p, "score", 0)
                    point_id = getattr(p, "id", idx)
                
                # Deduplication: skip if we've seen this incident
                incident_id = (payload or {}).get("incident_id")
                if incident_id and incident_id in seen_incident_ids:
                    continue
                if incident_id:
                    seen_incident_ids.add(incident_id)
                
                # Score adjustment for matching disaster types (clamped to prevent over-confidence)
                base_score = float(score) if score is not None else 0.0
                boosted_score = base_score
                if target_disaster_type and payload:
                    result_disaster_type = payload.get("disaster_type", "")
                    if result_disaster_type == target_disaster_type:
                        # Additive bonus instead of multiplicative to prevent score inflation
                        boosted_score = min(1.0, base_score + 0.05)  # 5% additive bonus, clamped
                    elif result_disaster_type:
                        boosted_score = base_score * 0.9  # 10% penalty for mismatch
                # Ensure score never exceeds 1.0
                boosted_score = min(1.0, max(0.0, boosted_score))
                
                normalized.append({
                    "id": point_id,
                    "score": boosted_score,
                    "original_score": float(score) if score is not None else 0.0,
                    "payload": payload if payload else {}
                })
            except Exception as e:
                print(f"    _normalize_results error for point {idx}: {e}")
                continue
        
        # Sort by boosted score (descending)
        normalized.sort(key=lambda x: x["score"], reverse=True)
        return normalized