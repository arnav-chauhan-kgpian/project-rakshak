import os
import sys
import csv
import uuid
from datetime import datetime
from pathlib import Path
from qdrant_client import models

# Fix Windows console encoding for Unicode output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from layers.ingestion.satellite import SatelliteAgent
from layers.ingestion.embedding import EmbeddingAgent
from layers.ingestion.sparse_embedding import SparseEmbeddingAgent
from layers.ingestion.metadata import MetadataAgent
from layers.ingestion.qdrant_upsert import QdrantUpsertAgent
from layers.ingestion.disaster_classifier import DisasterClassificationAgent

from layers.search.query_planner import QueryPlannerAgent
from layers.search.hybrid_search import SearchExecutionAgent
from layers.search.cross_transfer import CrossDisasterAgent
from layers.search.validator import RelevanceValidatorAgent

from layers.reasoning.synthesis import EvidenceSynthesisAgent
from layers.reasoning.llm_reasoning import LLMReasoningAgent
from layers.reasoning.confidence import ConfidenceControllerAgent
from layers.reasoning.explanation import ExplanationAgent
from layers.reasoning.priority import PriorityAgent
from layers.reasoning.report_generator import ReportGeneratorAgent

# New Advanced Layers
from layers.ingestion.stream_processor import StreamProcessor
from layers.safety.guardrails import PIIScrubber, BiasMonitor
from layers.learning.feedback import FeedbackAgent
from layers.ingestion.audio import AudioIngestionAgent
from layers.memory.memory_store import MemoryStore

from utils.qdrant_init import initialize_qdrant, get_qdrant_client


class CentralCoordinator:
    """Agent 15: Central Coordinator - Orchestrates all 14 agents for multimodal disaster response"""
    
    def __init__(self):
        """Initialize all agents and Qdrant client"""
        try:
            # Initialize Qdrant client (uses .env config for Cloud or local)
            self.client = get_qdrant_client()
            
            # Initialize all agents
            self.agents = {
                # Layer 0: Classification Gate
                "classifier": DisasterClassificationAgent(confidence_threshold=0.4),
                
                # Layer 1: Ingestion
                "satellite": SatelliteAgent(),
                "embedder": EmbeddingAgent(),
                "sparse_embedder": SparseEmbeddingAgent(),
                "metadata": MetadataAgent(),
                "audio": AudioIngestionAgent(),
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
                "priority": PriorityAgent(self.client),
                "report_generator": ReportGeneratorAgent(),
                
                # Layer 4: Memory
                "memory": MemoryStore(self.client),
                
                # Layer 5: Safety (PII & Bias)
                "pii": PIIScrubber(),
                "bias": BiasMonitor(),
            }
            # Layer 6: Feedback (Needs memory access)
            self.agents["feedback"] = FeedbackAgent(self.agents["memory"])
            
            # Streaming Processor
            self.stream_processor = StreamProcessor(self)
            print("✓ CentralCoordinator initialized with 17 agents (multimodal + memory + classifier)")
        except Exception as e:
            print(f"Error initializing CentralCoordinator: {e}")

    def process_new_incident(self, image_path, latitude, longitude, disaster_type, incident_id="Incident_001", audio_path=None):
        """
        Main orchestration pipeline: Process new disaster incident through all layers.
        
        Args:
            image_path: Path to satellite image
            latitude: Incident latitude
            longitude: Incident longitude
            disaster_type: Type of disaster (earthquake, flood, wildfire, hurricane)
            incident_id: Unique incident identifier
            audio_path: Optional path to associated audio (911 call, radio log)
            
        Returns:
            Dictionary with complete assessment: report, priority, explanation
        """
        try:
            print(f"\n{'='*70}")
            print(f"Processing Incident: {incident_id} | Type: {disaster_type}")
            print(f"Location: Lat {latitude:.4f}, Lon {longitude:.4f}")
            if audio_path:
                print(f"Audio Input: {audio_path}")
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
            
            # Agent 0: Disaster Classification Gate
            print("  Agent 0: Disaster classification gate...")
            classification = self.agents["classifier"].classify(image_path)
            if not classification["is_disaster"]:
                print(f"    ✗ NOT A DISASTER IMAGE (confidence: {classification['confidence']:.2f})")
                return {
                    "incident_id": incident_id,
                    "status": "REJECTED",
                    "reason": "Image does not appear to show disaster damage",
                    "classification": classification
                }
            print(f"    ✓ Classified as disaster: {classification['disaster_type']} (confidence: {classification['confidence']:.2f})")
            
            # Agent 3: Parse metadata
            print("  Agent 3: Metadata JSON parsing...")
            metadata = self.agents["metadata"].parse_metadata(image_path, aoi_bounds, disaster_type)
            # Agent 14a: PII Redaction
            metadata = self.agents["pii"].scrub_metadata(metadata)
            # damage_severity and confidence_score are now extracted by MetadataAgent
            # No hardcoded overrides - using real analysis values
            print(f"    ✓ Metadata parsed: {metadata.get('disaster_type')} incident")
            
            # Agent 2b (Audio): Process audio if provided
            if audio_path and Path(audio_path).exists():
                print("  Agent 2b (Audio): Audio ingestion & transcription...")
                audio_result = self.agents["audio"].process_audio(audio_path)
                if audio_result:
                    # Enriched metadata with audio info
                    metadata["audio_transcript"] = audio_result.get("transcription", "")
                    metadata["audio_embedding"] = audio_result.get("embedding", [])
                    metadata["audio_duration"] = audio_result.get("duration", 0)
                    print(f"    ✓ Audio processed ({metadata['audio_duration']:.1f}s): {metadata['audio_transcript'][:50]}...")
            
            # Agent 2c: Generate sparse BM25 embeddings from metadata (now includes transcript if available)
            print("  Agent 2c: BM25 sparse embedding generation...")
            sparse_embedding = self.agents["sparse_embedder"].get_sparse_embedding(metadata)
            print(f"    ✓ Sparse embedding: {len(sparse_embedding.indices)} tokens")
            
            # Agent 4: Upsert to Qdrant memory (multimodal)
            print("  Agent 4: Qdrant multimodal memory upsert...")
            upsert_success = self.agents["upsert"].upsert_to_memory(
                embedding, metadata, incident_id, sparse_vector=sparse_embedding
            )
            if upsert_success:
                print(f"    ✓ Incident stored in vector database (dense + sparse + audio)")
            
            # ===== LAYER 2: RETRIEVAL / SEARCH =====
            print("\n[LAYER 2: RETRIEVAL]")
            
            # Agent 5: Plan query
            print("  Agent 5: Query planning...")
            plan = self.agents["planner"].plan_query(latitude, longitude, disaster_type)
            print(f"    ✓ Search plan: {plan.get('spatial_filter', {}).get('radius_km')}km radius, "
                  f"{plan.get('max_results')} results max")
            
            # Agent 6: Execute multimodal hybrid search (dense + sparse + metadata)
            print("  Agent 6: Multimodal hybrid search (image + text)...")
            # Reuse sparse_embedding from ingestion (same metadata context)
            raw_results = self.agents["searcher"].execute_search(
                embedding, latitude, longitude, plan, sparse_query_vector=sparse_embedding, exclude_incident_id=incident_id
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
            report = self.agents["llm"].generate_report(incident_id, refined_results, current_metadata=metadata)
            print(f"    ✓ Damage assessment report generated ({len(report)} chars)")
            
            # Agent 11: Calculate confidence
            print("  Agent 11: Confidence score calibration...")
            base_confidence = refined_results[0]["score"] if refined_results else 0.5
            adjusted_quality = quality_metrics.get('quality_score', 0.5)
            conf_score = self.agents["confidence"].calculate(base_confidence, adjusted_quality, quality_metrics)
            print(f"    ✓ Calibrated confidence: {conf_score:.2%}")
            
            # Agent 12: Generate visual explanation
            print("  Agent 12: Visual explanation package...")
            explanation = self.agents["explanation"].generate_explanation(
                report, patterns, conf_score, incident_id=incident_id
            )
            print(f"    ✓ Explanation package with {len(explanation.get('components', {}))} visual components")
            
            # Agent 13: Recommend triage priority
            print("  Agent 13: Triage priority recommendation (Hybrid RAG)...")
            # Confidence factor derived from quality metrics (consistency_ratio provides adjustment)
            confidence_factor = 1.0 + quality_metrics.get('consistency_ratio', 0.5)
            triage = self.agents["priority"].recommend(patterns.get('mode'), confidence_factor, incident_embedding=embedding)
            
            # Agent 14b: Bias Check (Output Guardrail)
            fairness = self.agents["bias"].check_fairness(triage)
            if not fairness["is_fair"]:
                 print(f"    ⚠ BIAS DETECTED: {fairness['reason']}")
            triage["fairness"] = fairness
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
            
            # Agent 14: Generate markdown report
            print("\n  Agent 14: Generating markdown report...")
            report_content, report_path = self.agents["report_generator"].generate_report(final_output)
            if report_path:
                print(f"    ✓ Report saved to: {report_path}")
                final_output["report_path"] = str(report_path)
            
            # Agent 15: Store to Long-Term Memory
            print("\n  Agent 15: Storing to long-term memory...")
            try:
                # Store to context memory (session-based)
                context_id = self.agents["memory"].store(
                    memory_type="context",
                    content=f"Incident {incident_id}: {disaster_type} at ({latitude}, {longitude})",
                    embedding=embedding,
                    importance_score=conf_score,
                    session_id=incident_id,
                    source_incident_id=incident_id,
                    tags=[disaster_type, patterns.get("mode", "unknown")]
                )
                print(f"    ✓ Context memory stored: {context_id[:8]}...")
                
                # Store to history memory (interaction log)
                history_id = self.agents["memory"].store(
                    memory_type="history",
                    content=report[:500] if report else "Assessment completed",
                    embedding=embedding,
                    importance_score=0.5,
                    source_incident_id=incident_id,
                    tags=["assessment", disaster_type],
                    metadata={
                        "confidence_score": conf_score,
                        "priority_level": triage.get("priority_level"),
                        "result_count": quality_metrics.get("result_count", 0)
                    }
                )
                print(f"    ✓ History memory stored: {history_id[:8]}...")
                
                # Store high-confidence findings to knowledge (permanent)
                if conf_score > 0.7:
                    knowledge_id = self.agents["memory"].store(
                        memory_type="knowledge",
                        content=f"Pattern: {disaster_type} - {patterns.get('mode')} damage mode",
                        embedding=embedding,
                        importance_score=conf_score,
                        source_incident_id=incident_id,
                        tags=[disaster_type, "pattern", patterns.get("mode", "unknown")]
                    )
                    print(f"    ✓ Knowledge memory stored: {knowledge_id[:8]}...")
                
                final_output["memory_ids"] = {
                    "context": context_id,
                    "history": history_id
                }
            except Exception as mem_err:
                print(f"    ⚠ Memory storage warning: {mem_err}")
            
            # Agent 15b: Process Memory Decay (active evolution)
            # Run probabilistically to reduce overhead (10% of calls)
            import random
            if random.random() < 0.1:
                try:
                    decayed_ctx = self.agents["memory"].apply_decay_batch("context")
                    decayed_hist = self.agents["memory"].apply_decay_batch("history")
                    # Clean up expired
                    self.agents["memory"].cleanup_expired("context")
                except Exception:
                    pass  # Background maintenance
            
            return final_output
            
        except Exception as e:
            print(f"\n❌ Error processing incident: {e}")
            import traceback
            traceback.print_exc()
            return {"incident_id": incident_id, "status": "ERROR", "error": str(e)}

    # ===== NEW: STREAMING & FEEDBACK API =====
    def start_streaming(self):
        """Starts background streaming ingestion."""
        self.stream_processor.start()

    def stop_streaming(self):
        """Stops background streaming ingestion."""
        self.stream_processor.stop()

    def submit_feedback(self, incident_id, score, comment):
        """
        Public API for RLHF Feedback Loop.
        Enables users/supervisors to reinforce or correct system decisions.
        """
        return self.agents["feedback"].process_feedback(incident_id, score, comment)

    def batch_ingest_xbd_data(self, data_dir="train", limit=None, max_workers=4):
        """
        Batch ingest xBD dataset images and labels into Qdrant with multi-threading.
        
        Args:
            data_dir: Path to test data directory with images/ and labels/ folders
            limit: Maximum number of images to process (None = all)
            max_workers: Number of parallel worker threads (default: 4)
        """
        from pathlib import Path
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time
        
        print(f"\n{'='*70}")
        print("BATCH INGESTION: xBD Disaster Dataset (Multi-threaded)")
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
        
        total_images = len(image_files)
        print(f"Found {total_images} post-disaster images to process")
        print(f"Using {max_workers} worker threads for parallel processing\n")
        
        start_time = time.time()
        success_count = 0
        error_count = 0
        processed_count = 0
        
        # Thread-safe counter for progress tracking
        import threading
        lock = threading.Lock()
        
        def process_image(img_path_idx):
            """Process a single image (runs in thread)."""
            img_path, idx = img_path_idx
            nonlocal success_count, error_count, processed_count
            
            try:
                # Generate incident ID from filename
                incident_id = img_path.stem.replace("_post_disaster", "")
                
                # Parse metadata to get disaster type and coordinates
                metadata = self.agents["metadata"].parse_metadata(str(img_path))
                disaster_type = metadata.get("disaster_type", "unknown")
                geoloc = metadata.get("geolocation", {})
                
                # Calculate centroid
                lat = (geoloc.get("lat_min", 0) + geoloc.get("lat_max", 0)) / 2
                lon = (geoloc.get("lon_min", 0) + geoloc.get("lon_max", 0)) / 2
                
                # Extract embedding (can be parallelized well)
                embedding = self.agents["embedder"].get_embedding(str(img_path))
                
                # Extract sparse embedding from metadata
                sparse_embedding = self.agents["sparse_embedder"].get_sparse_embedding(metadata)
                
                # Confidence score is computed from actual metadata analysis
                # No hardcoded override needed
                
                # Upsert to Qdrant (multimodal) - needs thread-safe client
                upsert_success = self.agents["upsert"].upsert_to_memory(
                    embedding, 
                    metadata, 
                    incident_id,
                    sparse_vector=sparse_embedding
                )
                
                with lock:
                    processed_count += 1
                    if upsert_success:
                        success_count += 1
                        print(f"  [{processed_count}/{total_images}] ✓ {incident_id} ({disaster_type})")
                    else:
                        error_count += 1
                        print(f"  [{processed_count}/{total_images}] ❌ {incident_id} (upsert failed)")
                
                return {"success": upsert_success, "incident_id": incident_id}
                    
            except Exception as e:
                with lock:
                    processed_count += 1
                    error_count += 1
                    print(f"  [{processed_count}/{total_images}] ❌ Error processing {img_path.stem}: {e}")
                return {"success": False, "error": str(e)}
        
        # Process images in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(process_image, (img_path, idx)): img_path 
                for idx, img_path in enumerate(image_files, 1)
            }
            
            # Wait for all to complete
            for future in as_completed(futures):
                try:
                    future.result()  # Get result to catch any exceptions
                except Exception as e:
                    with lock:
                        error_count += 1
                        print(f"  ❌ Thread error: {e}")
        
        elapsed_time = time.time() - start_time
        
        # Summary
        print(f"\n{'='*70}")
        print("BATCH INGESTION SUMMARY")
        print(f"{'='*70}")
        print(f"✓ Successfully ingested: {success_count} images")
        print(f"❌ Errors: {error_count} images")
        print(f"Total processed: {success_count + error_count} images")
        print(f"⏱ Time elapsed: {elapsed_time:.2f} seconds")
        print(f"⚡ Throughput: {(success_count + error_count) / elapsed_time:.2f} images/second\n")

    def batch_ingest_audio(self, metadata_path="911_metadata.csv", data_dir="train_audio"):
        """Ingest Audio logs from CSV."""
        print(f"\n{'='*70}")
        print("AUDIO INGESTION: 911 Dispatch Logs (Dual-Path)")
        print(f"{'='*70}\n")
        
        meta_file = Path(data_dir) / metadata_path if data_dir else Path(metadata_path)
        if not meta_file.exists(): 
            # Try 911_recordings subdir
            meta_file = Path(data_dir) / "911_recordings" / metadata_path
            
        if not meta_file.exists():
            # Try root if not in data_dir
            meta_file = Path(metadata_path)
            
        if not meta_file.exists():
            print(f"❌ Metadata CSV not found: {meta_file} (Checked {data_dir}, {data_dir}/911_recordings/, and root)")
            return

        print(f"Reading metadata from: {meta_file}")
        
        success = 0
        with open(meta_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            total = len(rows)
            print(f"Found {total} records. Processing...")
            
            for i, row in enumerate(rows):
                try:
                    # File Name usually in 'file_name' or 'link'
                    fname = row.get("file_name") or Path(row.get("link", "")).name
                    # Look in data_dir/audio or just data_dir? 
                    # User said "data located in train directory". Assuming mixed or subfolder?
                    # I'll check train/fname and train/audio/fname
                    audio_path = Path(data_dir) / fname
                    if not audio_path.exists():
                        # Try subdirectory 911_recordings
                        audio_path = Path(data_dir) / "911_recordings" / fname
                        
                    if not audio_path.exists():
                        print(f"  ⚠ Audio file missing: {fname} (Checked {data_dir} and 911_recordings/)")
                        continue
                            
                    # Process
                    print(f"  [{i+1}/{total}] Processing {fname}...")
                    result = self.agents["audio"].process_audio(str(audio_path))
                    
                    if result:
                        # Extract Severity Metrics
                        # Handle empty strings safely
                        deaths = int(row.get("deaths") or 0)
                        potential = int(row.get("potential_death") or 0)
                        panic_score = (deaths * 1.0 + potential * 0.5) / 5.0 # Crude normalization
                        panic_score = min(1.0, panic_score)
                        
                        # Upsert
                        # We use a UUID derived from ID to ensure validity in Qdrant
                        raw_id = f"audio_{row.get('id', i)}"
                        inc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, raw_id))
                        
                        point = models.PointStruct(
                            id=inc_id,
                            vector={
                                "audio": result["embedding"],
                                # We can optionally add text embedding for Description
                                # But for now, let's stick to audio vector + metadata
                            },
                            payload={
                                "transcript": result["transcription"],
                                "duration": result["duration"],
                                "deaths": deaths,
                                "potential_death": potential,
                                "panic_score": panic_score,
                                "description": row.get("description", ""),
                                "title": row.get("title", ""),
                                "type": "audio_log"
                            }
                        )
                        
                        self.client.upsert(
                            collection_name="disaster_memory",
                            points=[point]
                        )
                        success += 1
                        print(f"    ✓ Ingested (Panic Score: {panic_score:.2f})")
                        
                except Exception as e:
                    print(f"    ❌ Error: {e}")
                    
        print(f"\nAudio Ingestion Complete. {success}/{total} processed.")


def main():
    """Demo execution of the Multi-Agent Disaster Response System"""
    print("""
    +================================================================+
    |     MULTI-AGENT DISASTER RESPONSE SYSTEM (MAS)                |
    |     16 Agents | 4 Layers | Memory-Enhanced Workflows          |
    +================================================================+
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
        
        # Check for batch ingestion mode (can be combined with main logic)
        if "--batch-ingest" in sys.argv:
            print("\n" + "="*70)
            print("BATCH INGESTION MODE: Processing xBD Dataset")
            print("="*70 + "\n")
            coordinator.batch_ingest_xbd_data()
        elif "--ingest-audio" in sys.argv:
            print("\n" + "="*70)
            print("AUDIO INGESTION MODE")
            print("="*70 + "\n")
            coordinator.batch_ingest_audio()
        elif "--ingest-all" in sys.argv:
            print("\n" + "="*70)
            print("FULL INGESTION MODE (Images + Audio)")
            print("="*70 + "\n")
            coordinator.batch_ingest_xbd_data()
            coordinator.batch_ingest_audio()
        else:
            # Demo single incident (with audio)
            print("\n✅ Executing Demo Incident with Audio...")
            result = coordinator.process_new_incident(
                image_path="imagery/sample_earthquake_damage.png",
                latitude=34.0522,
                longitude=-118.2437,
                disaster_type="earthquake",
                incident_id=f"Incident_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                audio_path="train_audio/911_recordings/call_1.mp3" 
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
