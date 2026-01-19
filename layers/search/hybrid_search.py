import math
import numpy as np
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

class SearchExecutionAgent:
    """Agent 6: Qdrant Search Executor - Performs multimodal hybrid search (dense + sparse + metadata)"""
    
    def __init__(self, qdrant_client):
        self.client = qdrant_client
        self.collection_name = "disaster_memory"
    
    def _manual_rrf_fusion(self, dense_results, sparse_results, k=60):
        """
        Manually fuse dense and sparse search results using Reciprocal Rank Fusion (RRF).
        RRF score = sum(1 / (k + rank)) for each result across all rankings.
        
        Args:
            dense_results: List of dense search results
            sparse_results: List of sparse search results
            k: RRF parameter (constant, typically 60)
            
        Returns:
            Fused results sorted by RRF score
        """
        rrf_scores = {}
        
        # Score dense results
        for rank, result in enumerate(dense_results or []):
            result_id = result.get("id")
            if result_id not in rrf_scores:
                rrf_scores[result_id] = {"id": result_id, "payload": result.get("payload"), "rrf_score": 0}
            rrf_scores[result_id]["rrf_score"] += 1.0 / (k + rank + 1)
        
        # Score sparse results
        for rank, result in enumerate(sparse_results or []):
            result_id = result.get("id")
            if result_id not in rrf_scores:
                rrf_scores[result_id] = {"id": result_id, "payload": result.get("payload"), "rrf_score": 0}
            rrf_scores[result_id]["rrf_score"] += 1.0 / (k + rank + 1)
        
        # Convert to list and sort by RRF score
        fused = sorted(rrf_scores.values(), key=lambda x: x["rrf_score"], reverse=True)
        
        # Normalize RRF score back to 0-1 range for compatibility
        if fused:
            max_rrf = fused[0]["rrf_score"]
            for result in fused:
                result["score"] = result["rrf_score"] / max_rrf if max_rrf > 0 else 0
        
        return fused
    
    def execute_search(self, query_vector, latitude, longitude, plan, sparse_query_vector=None, exclude_incident_id=None):
        """
        Executes hybrid search: dense vectors + metadata filtering.
        Bypasses complex named vector logic to ensure compatibility.
        
        Args:
            query_vector: Dense query embedding (768-dimensional DINOv2)
            latitude: Center latitude for spatial search
            longitude: Center longitude for spatial search
            plan: Search plan from QueryPlannerAgent
            sparse_query_vector: Sparse query vector (BM25) - optional (not used for now)
            exclude_incident_id: Optional incident ID to exclude from results (self-match prevention)
            
        Returns:
            List of search results with fused scores
        """
        try:
            # Build spatial filter based on plan
            spatial_radius_km = plan.get("spatial_filter", {}).get("radius_km", 50)
            lat_delta = spatial_radius_km / 111.0  # Rough conversion: 1 degree = 111 km
            
            filter_obj = Filter(
                must=[
                    FieldCondition(
                        key="disaster_type",
                        match=MatchValue(value=plan.get("disaster_filter"))
                    ),
                    FieldCondition(
                        key="latitude",
                        range=Range(
                            gte=latitude - lat_delta,
                            lte=latitude + lat_delta
                        )
                    ),
                    FieldCondition(
                        key="longitude",
                        range=Range(
                            gte=longitude - lat_delta,
                            lte=longitude + lat_delta
                        )
                    )
                ],
                must_not=[
                    FieldCondition(
                        key="incident_id",
                        match=MatchValue(value=exclude_incident_id)
                    )
                ] if exclude_incident_id else []
            )
            
            results = []

            # Try dense search with filters (if method available)
            try:
                if hasattr(self.client, "search_points"):
                    # Try named vector "image" first
                    try:
                        dense_results = self.client.search_points(
                            collection_name=self.collection_name,
                            query_vector=("image", query_vector),
                            query_filter=filter_obj,
                            limit=plan.get("max_results", 10)
                        ).points
                        results = self._normalize_results(dense_results)
                    except Exception as named_err:
                        # Fallback to unnamed vector search
                        print(f"  Named vector search failed, trying unnamed: {named_err}")
                        dense_results = self.client.search_points(
                            collection_name=self.collection_name,
                            query_vector=query_vector,
                            query_filter=filter_obj,
                            limit=plan.get("max_results", 10)
                        ).points
                        results = self._normalize_results(dense_results)
            except Exception as e:
                print(f"  Search with filters error: {e}")
                results = []

            # Robust Python-side fallback if client lacks search APIs or returns empty
            if not results:
                try:
                    results = self._python_fallback_search(query_vector, filter_obj, plan, exclude_incident_id)
                except Exception as e:
                    print(f"  Python fallback search error: {e}")
                    results = []
            
            return results
            
        except Exception as e:
            print(f"Hybrid Search Error: {e}")
            return []

    def _normalize_results(self, points):
        """Convert Qdrant ScoredPoint objects (or dicts) into plain dicts for downstream agents."""
        normalized = []
        for idx, p in enumerate(points or []):
            try:
                # Support both attribute-style (ScoredPoint) and dict results
                payload = getattr(p, "payload", None) or p.get("payload", {})
                score = getattr(p, "score", None)
                if score is None:
                    score = p.get("score", 0)
                point_id = getattr(p, "id", None) or p.get("id") or idx
                normalized.append({
                    "id": point_id,
                    "score": float(score),
                    "payload": payload,
                    "vector_name": getattr(p, "vector_name", None) or p.get("vector_name")
                })
            except Exception:
                continue
        return normalized

    def _python_fallback_search(self, query_vector, filter_obj, plan, exclude_incident_id=None):
        """
        Fallback search that scrolls all points and computes cosine similarity in Python.
        Applies metadata filters (disaster_type, latitude/longitude range) and returns top results.
        Also excludes the current incident if `exclude_incident_id` is provided.
        """
        # Fetch all points with payload and vectors
        all_points = []
        next_offset = None
        max_fetch = 10000  # large enough for typical datasets

        while True:
            # Use server-side filter if available to reduce scan size
            kwargs = {
                "collection_name": self.collection_name,
                "limit": max_fetch,
                "with_payload": True,
                "with_vectors": True,
                "offset": next_offset
            }
            try:
                # Newer clients support 'scroll' with 'filter' param
                kwargs["filter"] = filter_obj
            except Exception:
                pass
            res = self.client.scroll(**kwargs)
            points_batch, next_offset = res
            if points_batch:
                all_points.extend(points_batch)
            if not next_offset:
                break

        # Convert query vector to numpy
        q = np.asarray(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm == 0:
            return []
        q = q / q_norm

        # Spatial filter bounds
        latitude = plan.get("center_lat")
        longitude = plan.get("center_lon")
        spatial_radius_km = plan.get("spatial_filter", {}).get("radius_km", 50)
        lat_delta = spatial_radius_km / 111.0
        lon_delta = lat_delta
        target_disaster = plan.get("disaster_filter")

        # Compute scores and filter
        scored = []
        for p in all_points:
            payload = getattr(p, "payload", {})
            # Exclude self incident if requested
            if exclude_incident_id and payload.get("incident_id") == exclude_incident_id:
                continue
            # Apply disaster type filter (if specified)
            if target_disaster and payload.get("disaster_type") != target_disaster:
                continue
            # Apply spatial filter (if lat/lon present)
            lat = payload.get("latitude")
            lon = payload.get("longitude")
            if lat is not None and lon is not None:
                if not (latitude - lat_delta <= lat <= latitude + lat_delta and
                        longitude - lon_delta <= lon <= longitude + lon_delta):
                    continue

            # Get vector (supports both attribute and dict forms)
            vec = getattr(p, "vector", None) or getattr(p, "vectors", None)
            if isinstance(vec, dict):
                # If dict, try common keys
                vec = vec.get("image") or vec.get("default") or list(vec.values())[0]
            if vec is None:
                continue

            v = np.asarray(vec, dtype=np.float32)
            v_norm = np.linalg.norm(v)
            if v_norm == 0:
                continue
            v = v / v_norm
            # Cosine similarity
            sim = float(np.dot(q, v))

            scored.append({
                "id": getattr(p, "id", None),
                "score": sim,
                "payload": payload
            })

        # Sort by similarity
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:plan.get("max_results", 10)]