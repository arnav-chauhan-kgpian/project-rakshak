import os
from layers.ingestion.satellite import SatelliteAgent
from layers.ingestion.embedding import EmbeddingAgent
from layers.ingestion.sparse_embedding import SparseEmbeddingAgent
from layers.ingestion.metadata import MetadataAgent
from layers.ingestion.qdrant_upsert import QdrantUpsertAgent

from layers.search.query_planner import QueryPlannerAgent
from layers.search.hybrid_search import SearchExecutionAgent
from layers.search.cross_transfer import CrossDisasterAgent
from layers.search.validator import RelevanceValidatorAgent

from layers.reasoning.synthesis import EvidenceSynthesisAgent
from layers.reasoning.llm_reasoning import LLMReasoningAgent
from layers.reasoning.confidence import ConfidenceControllerAgent
from layers.reasoning.explanation import ExplanationAgent
from layers.reasoning.priority import PriorityAgent

from utils.qdrant_init import initialize_qdrant
from qdrant_client import QdrantClient


class CentralCoordinator:
    """Agent 15: Central Coordinator - Orchestrates all 14 agents for multimodal disaster response"""
    
    def __init__(self):
        """Initialize all agents and Qdrant client"""
        try:
            # Initialize Qdrant client
            self.client = QdrantClient("localhost", port=6333)
            
            # Initialize all agents
            self.agents = {
                # Layer 1: Ingestion
                "satellite": SatelliteAgent(),
                "embedder": EmbeddingAgent(),
                "sparse_embedder": SparseEmbeddingAgent(),
                "metadata": MetadataAgent(),
                "upsert": QdrantUpsertAgent(self.client),
                
                # Layer 2: Search/Retrieval
                "planner": QueryPlannerAgent(),
                "searcher": SearchExecutionAgent(self.client),
                "transfer": CrossDisasterAgent(),
                "validator": RelevanceValidatorAgent(),
                
                # Layer 3: Reasoning
                "synthesizer": EvidenceSynthesisAgent(),
                "llm": LLMReasoningAgent(),
                "confidence": ConfidenceControllerAgent(),
                "explanation": ExplanationAgent(),
                "priority": PriorityAgent()
            }
            print("✓ CentralCoordinator initialized with all 14 agents (multimodal)")
        except Exception as e:
            print(f"Error initializing CentralCoordinator: {e}")

    def process_new_incident(self, image_path, latitude, longitude, disaster_type, incident_id="Incident_001"):
        """
        Main orchestration pipeline: Process new disaster incident through all layers.
        
        Args:
            image_path: Path to satellite image
            latitude: Incident latitude
            longitude: Incident longitude
            disaster_type: Type of disaster (earthquake, flood, wildfire, hurricane)
            incident_id: Unique incident identifier
            
        Returns:
            Dictionary with complete assessment: report, priority, explanation
        """
        try:
            print(f"\n{'='*70}")
            print(f"Processing Incident: {incident_id} | Type: {disaster_type}")
            print(f"Location: Lat {latitude:.4f}, Lon {longitude:.4f}")
            print(f"{'='*70}")
            
            # ===== LAYER 1: PERCEPTION / INGESTION =====
            print("\n[LAYER 1: PERCEPTION]")
            
            # Agent 1: Download satellite imagery
            print("  Agent 1: Satellite imagery ingestion...")
            aoi_bounds = {
                "lat_min": latitude - 0.05,
                "lat_max": latitude + 0.05,
                "lon_min": longitude - 0.05,
                "lon_max": longitude + 0.05
            }
            imagery = self.agents["satellite"].download_imagery(aoi_bounds)
            print(f"    ✓ Imagery downloaded: {len(imagery)} tiles")
            
            # Agent 2: Extract DINOv2 embeddings
            print("  Agent 2: DINOv2 embedding extraction...")
            embedding = self.agents["embedder"].get_embedding(image_path)
            print(f"    ✓ Embedding generated: {len(embedding)}-dimensional vector")
            
            # Agent 3: Parse metadata
            print("  Agent 3: Metadata JSON parsing...")
            metadata = self.agents["metadata"].parse_metadata(image_path, aoi_bounds, disaster_type)
            metadata["damage_severity"] = "high"  # Mock severity
            metadata["confidence_score"] = 0.75
            print(f"    ✓ Metadata parsed: {metadata.get('disaster_type')} incident")
            
            # Agent 2b: Generate sparse BM25 embeddings from metadata
            print("  Agent 2b: BM25 sparse embedding generation...")
            sparse_embedding = self.agents["sparse_embedder"].get_sparse_embedding(metadata)
            print(f"    ✓ Sparse embedding: {len(sparse_embedding.indices)} tokens")
            
            # Agent 4: Upsert to Qdrant memory (multimodal)
            print("  Agent 4: Qdrant multimodal memory upsert...")
            upsert_success = self.agents["upsert"].upsert_to_memory(
                embedding, metadata, incident_id, sparse_vector=sparse_embedding
            )
            if upsert_success:
                print(f"    ✓ Incident stored in vector database (dense + sparse)")
            
            # ===== LAYER 2: RETRIEVAL / SEARCH =====
            print("\n[LAYER 2: RETRIEVAL]")
            
            # Agent 5: Plan query
            print("  Agent 5: Query planning...")
            plan = self.agents["planner"].plan_query(latitude, longitude, disaster_type)
            print(f"    ✓ Search plan: {plan.get('spatial_filter', {}).get('radius_km')}km radius, "
                  f"{plan.get('max_results')} results max")
            
            # Agent 6: Execute multimodal hybrid search (dense + sparse + metadata)
            print("  Agent 6: Multimodal hybrid search (image + text)...")
            # Create sparse query from metadata text
            sparse_query = self.agents["sparse_embedder"].get_sparse_embedding(metadata)
            raw_results = self.agents["searcher"].execute_search(
                embedding, latitude, longitude, plan, sparse_query_vector=sparse_query, exclude_incident_id=incident_id
            )
            print(f"    ✓ Retrieved {len(raw_results)} similar incidents (RRF fusion)")
            
            # Agent 7: Apply cross-disaster transfer learning
            print("  Agent 7: Cross-disaster transfer penalty...")
            refined_results = self.agents["transfer"].apply_penalty(raw_results, disaster_type)
            print(f"    ✓ Penalties applied based on disaster type similarity")
            
            # Agent 8: Validate quality
            print("  Agent 8: Relevance validation...")
            status, quality_metrics = self.agents["validator"].validate(refined_results)
            print(f"    ✓ Validation: {status} | Quality Score: {quality_metrics.get('quality_score', 0):.2f}")
            
            if status == "REJECT":
                return {
                    "incident_id": incident_id,
                    "status": "REJECTED",
                    "reason": "Insufficient evidence quality",
                    "quality_metrics": quality_metrics
                }
            
            # ===== LAYER 3: REASONING =====
            print("\n[LAYER 3: REASONING]")
            
            # Agent 9: Synthesize evidence patterns
            print("  Agent 9: Evidence synthesis & pattern analysis...")
            patterns = self.agents["synthesizer"].analyze_patterns(refined_results)
            print(f"    ✓ Primary damage mode: {patterns.get('mode')} | "
                  f"Results: {patterns.get('result_count')}")
            
            # Agent 10: Generate LLM-based report
            print("  Agent 10: LLM reasoning & citation...")
            report = self.agents["llm"].generate_report(incident_id, refined_results)
            print(f"    ✓ Damage assessment report generated ({len(report)} chars)")
            
            # Agent 11: Calculate confidence
            print("  Agent 11: Confidence score calibration...")
            base_confidence = refined_results[0]["score"] if refined_results else 0.5
            adjusted_quality = quality_metrics.get('quality_score', 0.5) * min(1.0, quality_metrics.get('result_count', 0) / 3.0)
            conf_score = self.agents["confidence"].calculate(base_confidence, adjusted_quality)
            print(f"    ✓ Calibrated confidence: {conf_score:.2%}")
            
            # Agent 12: Generate visual explanation
            print("  Agent 12: Visual explanation package...")
            explanation = self.agents["explanation"].generate_explanation(report, patterns, conf_score)
            print(f"    ✓ Explanation package with {len(explanation.get('components', {}))} visual components")
            
            # Agent 13: Recommend triage priority
            print("  Agent 13: Triage priority recommendation...")
            triage = self.agents["priority"].recommend(patterns.get('mode'), 1.5)
            print(f"    ✓ Priority level: {triage.get('priority_level').upper()} | "
                  f"Response time: {triage.get('response_time_hours')}h")
            
            # ===== FINAL OUTPUT =====
            print(f"\n{'='*70}")
            print("ASSESSMENT COMPLETE")
            print(f"{'='*70}")
            
            final_output = {
                "incident_id": incident_id,
                "status": "COMPLETED",
                "location": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "disaster_type": disaster_type,
                "damage_assessment_report": report,
                "triage_priority_map": triage,
                "confidence_score": conf_score,
                "explanation_package": explanation,
                "quality_metrics": quality_metrics,
                "patterns": patterns
            }
            
            return final_output
            
        except Exception as e:
            print(f"\n❌ Error processing incident: {e}")
            import traceback
            traceback.print_exc()
            return {"incident_id": incident_id, "status": "ERROR", "error": str(e)}
    
    def batch_ingest_xbd_data(self, data_dir="data/test", limit=None):
        """
        Batch ingest xBD dataset images and labels into Qdrant.
        
        Args:
            data_dir: Path to test data directory with images/ and labels/ folders
            limit: Maximum number of images to process (None = all)
        """
        from pathlib import Path
        
        print(f"\n{'='*70}")
        print("BATCH INGESTION: xBD Disaster Dataset")
        print(f"{'='*70}\n")
        
        # Locate image directory
        images_dir = Path(data_dir) / "images"
        labels_dir = Path(data_dir) / "labels"
        
        if not images_dir.exists():
            print(f"❌ Images directory not found: {images_dir}")
            return
        
        # Get all post-disaster images
        image_files = sorted(list(images_dir.glob("*_post_disaster.png")))
        
        if limit:
            image_files = image_files[:limit]
        
        print(f"Found {len(image_files)} post-disaster images to process\n")
        
        success_count = 0
        error_count = 0
        
        for idx, img_path in enumerate(image_files, 1):
            try:
                # Generate incident ID from filename
                incident_id = img_path.stem.replace("_post_disaster", "")
                
                print(f"\n[{idx}/{len(image_files)}] Processing: {incident_id}")
                
                # Parse metadata to get disaster type and coordinates
                metadata = self.agents["metadata"].parse_metadata(str(img_path))
                disaster_type = metadata.get("disaster_type", "unknown")
                geoloc = metadata.get("geolocation", {})
                
                # Calculate centroid
                lat = (geoloc.get("lat_min", 0) + geoloc.get("lat_max", 0)) / 2
                lon = (geoloc.get("lon_min", 0) + geoloc.get("lon_max", 0)) / 2
                
                print(f"  Type: {disaster_type} | Severity: {metadata.get('damage_severity')}")
                print(f"  Buildings: {metadata.get('total_buildings')} | Location: ({lat:.4f}, {lon:.4f})")
                
                # Extract embedding
                embedding = self.agents["embedder"].get_embedding(str(img_path))
                print(f"  ✓ Embedding extracted: {len(embedding)}-dim")
                
                # Extract sparse embedding from metadata
                sparse_embedding = self.agents["sparse_embedder"].get_sparse_embedding(metadata)
                print(f"  ✓ Sparse embedding: {len(sparse_embedding.indices)} tokens")
                
                # Add confidence score
                metadata["confidence_score"] = 0.75
                
                # Upsert to Qdrant (multimodal)
                upsert_success = self.agents["upsert"].upsert_to_memory(
                    embedding, 
                    metadata, 
                    incident_id,
                    sparse_vector=sparse_embedding
                )
                
                if upsert_success:
                    print(f"  ✓ Upserted to Qdrant collection")
                    success_count += 1
                else:
                    print(f"  ❌ Upsert failed")
                    error_count += 1
                    
            except Exception as e:
                print(f"  ❌ Error: {e}")
                error_count += 1
                continue
        
        # Summary
        print(f"\n{'='*70}")
        print("BATCH INGESTION SUMMARY")
        print(f"{'='*70}")
        print(f"✓ Successfully ingested: {success_count} images")
        print(f"❌ Errors: {error_count} images")
        print(f"Total processed: {success_count + error_count} images\n")


def main():
    """Demo execution of the Multi-Agent Disaster Response System"""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║     MULTI-AGENT DISASTER RESPONSE SYSTEM (MAS)                ║
    ║     14 Agents | 3 Layers | 13 Disaster Response Workflows     ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    import sys
    
    try:
        # Check for reset flag
        force_reset = "--reset" in sys.argv
        
        # Initialize Qdrant collection
        print("Initializing Qdrant vector database...")
        initialize_qdrant(force_recreate=force_reset)
        
        # Exit early if only resetting
        if force_reset and len(sys.argv) == 2:
            print("\n✓ Collection reset complete. Run 'python main.py --batch-ingest' to populate.")
            return
        
        # Initialize coordinator
        coordinator = CentralCoordinator()
        
        # Check for batch ingestion mode
        if len(sys.argv) > 1 and sys.argv[1] == "--batch-ingest":
            print("\n" + "="*70)
            print("BATCH INGESTION MODE: Processing xBD Dataset")
            print("="*70 + "\n")
            coordinator.batch_ingest_xbd_data()
        else:
            # Demo single incident
            result = coordinator.process_new_incident(
                image_path="imagery/sample_earthquake_damage.png",
                latitude=34.0522,
                longitude=-118.2437,
                disaster_type="earthquake",
                incident_id="EarthQuake_LA_2024_001"
            )
            
            # Print results
            print("\n" + "="*70)
            print("FINAL ASSESSMENT OUTPUT")
            print("="*70)
            import json
            print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
