import sys
sys.stdout.reconfigure(encoding='utf-8')
from ingest_audio import ingest_audio_folder
from layers.ingestion.satellite import SatelliteAgent
from layers.ingestion.embedding import EmbeddingAgent
from layers.ingestion.sparse_embedding import SparseEmbeddingAgent
from layers.ingestion.metadata import MetadataAgent
from layers.ingestion.qdrant_upsert import QdrantUpsertAgent

from layers.search.search_processor import SearchProcessorAgent  # Merged: Agents 5, 7, 8
from layers.search.hybrid_search import SearchExecutionAgent

from layers.reasoning.recomm import EvidenceSynthesisAgent
from layers.reasoning.geo_search import GeoSimilarityAgent
from layers.reasoning.history_summarizer import HistorySummarizerAgent
from layers.reasoning.llm_reasoning import LLMReasoningAgent
from layers.reasoning.evaluator import ReportAuditorAgent
from layers.reasoning.post_processor import PostProcessorAgent  # Merged: Agents 11-13

from utils.qdrant_init import initialize_qdrant, get_qdrant_client
from qdrant_client import QdrantClient


class CentralCoordinator:
    """Agent 15: Central Coordinator - Orchestrates all 14 agents for multimodal disaster response"""
    
    def __init__(self):
        """Initialize all agents and Qdrant client"""
        try:
            # Initialize Qdrant client (use same factory as init script)
            self.client = get_qdrant_client()
            
            # Initialize all agents
            self.agents = {
                # Layer 1: Ingestion
                "satellite": SatelliteAgent(),
                "embedder": EmbeddingAgent(),
                "sparse_embedder": SparseEmbeddingAgent(),
                "metadata": MetadataAgent(),
                "upsert": QdrantUpsertAgent(self.client),
                
                # Layer 2: Search (Merged)
                "search_processor": SearchProcessorAgent(),  # Merged: Agents 5, 7, 8
                "searcher": SearchExecutionAgent(self.client),
                
                # Layer 3: Reasoning
                "synthesizer": EvidenceSynthesisAgent(self.client),
                "geo_search": GeoSimilarityAgent(self.client),
                "history_summarizer": HistorySummarizerAgent(),
                "llm": LLMReasoningAgent(),
                "auditor": ReportAuditorAgent(),
                "post_processor": PostProcessorAgent()  # Merged: Confidence + Explanation + Priority
            }
            print("✓ CentralCoordinator initialized with 15 agents (Total System Architecture)")
        except Exception as e:
            print(f"Error initializing CentralCoordinator: {e}")

    def process_new_incident(self, image_path, latitude, longitude, disaster_type, incident_id="Incident_001", triage_override=None, audio_path=None):
        """
        Main orchestration pipeline: Process new disaster incident through all layers.
        
        Args:
            image_path: Path to satellite image
            latitude: Incident latitude
            longitude: Incident longitude
            disaster_type: Type of disaster
            incident_id: Unique incident identifier
            triage_override: Optional dict with panic score from chatbot
            audio_path: Optional path to audio file for analysis
        """
        try:
            print(f"\n{'='*70}")
            print(f"Processing Incident: {incident_id} | Type: {disaster_type}")
            print(f"Location: Lat {latitude:.4f}, Lon {longitude:.4f}")
            if triage_override:
                print(f"⚠ Triage Override Active: Panic Level {triage_override.get('panic_score', 'Unknown').upper()}")
            print(f"{'='*70}")
            
            # Helper: Load Audio Context if path provided
            audio_context = None
            if audio_path:
                print(f"  🎤 Analyizing Audio Evidence: {audio_path}...")
                # In production, use Whisper here. For now, simulate or read text file if exists.
                audio_context = {"transcript": "User reported loud explosion and trapped civilians.", "panic_score": "High"}
                try:
                    if os.path.exists(audio_path) and audio_path.endswith(".txt"):
                        with open(audio_path, 'r') as f:
                             audio_context["transcript"] = f.read().strip()
                except:
                    pass
            
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
            
            # ===== LAYER 2: RETRIEVAL / SEARCH (PARALLEL OPTIMIZED) =====
            print("\n[LAYER 2: RETRIEVAL - PARALLEL EXECUTION]")
            
            from utils.async_utils import run_parallel_tasks

            # Agent 5: Plan query
            print("  SearchProcessor: Query planning...")
            plan = self.agents["search_processor"].plan_query(latitude, longitude, disaster_type)
            print(f"    ✓ Search plan: {plan.get('spatial_filter', {}).get('radius_km')}km radius")
            
            # Define Parallel Tasks
            tasks = {
                # Task A: Strict Search for Damage Assessment (Apples-to-Apples)
                "visual_search_assessment": lambda: self.agents["searcher"].execute_search(
                    embedding, latitude, longitude, plan, 
                    sparse_query_vector=self.agents["sparse_embedder"].get_sparse_embedding(metadata), 
                    exclude_incident_id=incident_id,
                    disaster_type=disaster_type # Filter ENABLED for assessment accuracy
                ),
                # Task B: Broad Search for Historical Context (Visual Similarity Only)
                "visual_search_context": lambda: self.agents["searcher"].execute_search(
                    embedding, latitude, longitude, plan, 
                    sparse_query_vector=self.agents["sparse_embedder"].get_sparse_embedding(metadata), 
                    exclude_incident_id=incident_id
                    # disaster_type filter REMOVED for broad visual context
                ),
                # Task C: Geo Search
                "geo_search": lambda: self.agents["geo_search"].find_nearby_disasters(
                    latitude=latitude,
                    longitude=longitude,
                    radius_km=100,
                    limit=5,
                    exclude_incident_id=incident_id
                )
            }
            
            # Execute in Parallel
            print("  🚀 Launching Async Agents: [6: Visual Assessment] & [6b: Visual Context] & [9b: Geo Search]...")
            results = run_parallel_tasks(tasks)
            
            # Assessment Pipeline uses STRICT results
            raw_results = results.get("visual_search_assessment", [])
            
            # Historical Context uses BROAD results
            visual_context_results = results.get("visual_search_context", [])
            geo_similar = results.get("geo_search", [])

            print(f"    ✓ Parallel Execution Complete: {len(raw_results)} assessment matches | {len(visual_context_results)} context matches")

            # Agent 7: Apply cross-disaster transfer learning (via Processor)
            print("  SearchProcessor: Cross-disaster transfer penalty...")
            refined_results = self.agents["search_processor"].apply_penalty(raw_results, disaster_type)
            
            # Agent 8: Validate quality (via Processor)
            print("  SearchProcessor: Relevance validation...")
            status, quality_metrics = self.agents["search_processor"].validate(refined_results)
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
            
            # Agent 9a: Synthesize evidence patterns (Visual Similarity via Recommendation)
            print("  Agent 9a: Evidence synthesis & pattern analysis...")
            patterns = self.agents["synthesizer"].analyze_patterns(refined_results)
            print(f"    ✓ Primary damage mode: {patterns.get('mode')} | "
                  f"Results: {patterns.get('result_count')}")
            
            # Agent 10a: Summarize historical context (Stage 1 LLM)
            print("  Agent 10a: Historical context summarization...")
            # Use BROAD visual context results here
            history_summary = self.agents["history_summarizer"].summarize_history(
                visual_results=visual_context_results,
                geo_results=geo_similar,
                current_disaster_type=disaster_type
            )
            print(f"    ✓ Historical context summarized (visual + geo)")
            
            # Agent 10b: Generate final report (Stage 2 LLM)
            print("  Agent 10b: Final report generation...")
            # Pass ACTUAL incident metadata + summarized history (not raw data)
            incident_metadata = {
                "latitude": latitude,
                "longitude": longitude,
                "disaster_type": disaster_type,
                # INFERRED damage level from hybrid search consensus (Agent 9)
                "inferred_damage": patterns.get("mode", "unknown"),
                "damage_distribution": patterns.get("severity_distribution", {})
            }
            # Stage 2: Communicator (Generate draft)
            draft_report = self.agents["llm"].generate_report(
                incident_id, incident_metadata, history_summary, 
                audio_context=audio_context
            )
            
            # Agent 14: Auditor (Stage 3 LLM - NEW)
            # Fact-checks the draft against ground truth metadata
            print("  Agent 14: Final report evaluation & fact-checking...")
            final_report = self.agents["auditor"].audit_report(draft_report, incident_metadata)
            print(f"    ✓ Emergency report verified and corrected ({len(final_report)} chars)")
            
            # Use the verified report for the rest of parameters
            report = final_report
            
            # Post-Processing (Agents 11-13 Merged)
            print("  Post-Processor: Confidence + Explanation + Triage...")
            post_results = self.agents["post_processor"].process(
                report, patterns, quality_metrics, 
                triage_override=triage_override,
                incident_id=incident_id
            )
            conf_score = post_results["confidence_score"]
            explanation = post_results["explanation_package"]
            triage = post_results["triage_priority_map"]
            print(f"    ✓ Confidence: {conf_score:.2%} | Priority: {triage.get('priority_level', 'N/A').upper()}")
            
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
    
    def batch_ingest_xbd_data(self, data_dir="train", limit=None):
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


def summarize_chat_logs(active_logs=None, incident_lat=None, incident_lon=None, radius_km=50):
    """Summarizes chat logs for Rakshak Intel. Filters by geographic proximity if coords provided."""
    import json
    import math
    from pathlib import Path
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance between two points in km."""
        R = 6371  # Earth's radius in km
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    log_dir = Path("chat_logs")
    
    # Use session logs if provided, else check folder
    if active_logs is not None:
        all_logs = [Path(l) for l in active_logs if l and Path(l).exists()]
    else:
        if not log_dir.exists():
            return None
        all_logs = list(log_dir.glob("*.json"))
    
    if not all_logs:
        print("\n[Rakshak Intel] No distress signals in current session.")
        return None
    
    # Filter by proximity if incident coordinates provided
    logs = []
    for log in all_logs:
        try:
            with open(log, 'r') as f:
                data = json.load(f)
                risk_data = data.get("risk_assessment_init", {})
                log_lat = risk_data.get("lat")
                log_lon = risk_data.get("lon")
                
                # If we have incident coords, filter by distance
                if incident_lat is not None and incident_lon is not None and log_lat and log_lon:
                    dist = haversine_distance(incident_lat, incident_lon, log_lat, log_lon)
                    if dist <= radius_km:
                        logs.append((log, data, dist))
                else:
                    # No coords filter, include all
                    logs.append((log, data, 0))
        except:
            continue
    
    if not logs:
        print(f"\n[Guardian Intel] No distress signals within {radius_km}km of incident.")
        return None
    
    # Sort by distance (closest first)
    logs.sort(key=lambda x: x[2])
    
    print(f"\n[Rakshak Intel] Found {len(logs)} distress signals near incident (within {radius_km}km).")
    
    highest_panic = "Low"
    panic_map = {"Low": 0, "Medium": 1, "High": 2, "Extreme": 3}
    summary_text = []
    
    for log_path, data, dist in logs:
        try:
            report = json.loads(data.get("triage_report", "{}"))
            p_score = report.get("panic_score", "Low")
            
            if panic_map.get(p_score, 0) > panic_map.get(highest_panic, 0):
                highest_panic = p_score
                
            summary = report.get("summary", "")
            if summary:
                summary_text.append(f"- [{dist:.1f}km] {summary}")
        except:
            continue
            
    if not summary_text:
        return None
        
    print(f"[Rakshak Intel] Aggregated Panic Level: {highest_panic.upper()}")
    for s in summary_text[:3]:
        print(f"  {s}")
    
    return {
        "panic_score": highest_panic,
        "summary": "Aggregated Distress Signals: " + " ".join([s.split("] ")[1] for s in summary_text[:3]])
    }

def run_rakshak_assessment(coordinator=None, session_logs=None):
    """Interactively runs the full Rakshak Pipeline. Type 'j' to return to menu."""
    if not coordinator:
        coordinator = CentralCoordinator()
        
    print("\nRunning Rakshak Damage Assessment Pipeline...")
    print("(Type 'j' at any prompt to return to menu)\n")
    
    print("[RAKSHAK INTEL] Please input incident parameters (or press ENTER for Demo Defaults):")
    
    # Dynamic Input with Defaults
    def_lat = "34.0522"
    def_lon = "-118.2437"
    def_type = "volcano"
    def_id = "VOLCANO_GUATEMALA_2024_001"
    
    # 1. Latitude (First for Google Earth automation)
    lat_in = input(f"1. Latitude [Default: {def_lat}]: ").strip()
    if lat_in.lower() == 'j':
        print("Returning to menu...")
        return
    latitude = float(lat_in) if lat_in else float(def_lat)

    # 2. Longitude
    lon_in = input(f"2. Longitude [Default: {def_lon}]: ").strip()
    if lon_in.lower() == 'j':
        print("Returning to menu...")
        return
    longitude = float(lon_in) if lon_in else float(def_lon)
    
    # 3. Satellite Image (Automated Fetch)
    fetched_image = None
    try:
        print(f"\n[SYSTEM] Attempting to fetch live aerial imagery for ({latitude}, {longitude})...")
        fetched_image = coordinator.agents["satellite"].fetch_esri_satellite_image(latitude, longitude)
    except Exception as e:
        print(f"  ⚠ Auto-fetch failed: {e}")

    def_img = fetched_image if fetched_image else "imagery/guatemala-volcano_00000003_post_disaster.png"
    
    img_in = input(f"3. Satellite Image Path [Default: {def_img}]: ").strip()
    if img_in.lower() == 'j':
        print("Returning to menu...")
        return
    image_path = img_in if img_in else def_img

    # 4. Disaster Type
    type_in = input(f"4. Disaster Type [Default: {def_type}]: ").strip()
    if type_in.lower() == 'j':
        print("Returning to menu...")
        return
    disaster_type = type_in if type_in else def_type
    
    # 5. Incident ID
    id_in = input(f"5. Incident ID [Default: {def_id}]: ").strip()
    if id_in.lower() == 'j':
        print("Returning to menu...")
        return
    incident_id = id_in if id_in else def_id

    # Audio Evidence (Optional)
    print("\n[Optional] Enter path to related audio/distress call (or press Enter):")
    audio_in = input(f"6. Audio Path > ").strip()
    if audio_in.lower() == 'j':
        print("Returning to menu...")
        return
    audio_path = audio_in if audio_in else None

    # Check for Chat Log Intel (filter by proximity to this incident)
    triage_override = summarize_chat_logs(
        active_logs=session_logs, 
        incident_lat=latitude, 
        incident_lon=longitude
    )

    print(f"\n[SYSTEM] Initializing Analysis for: {incident_id} @ {latitude}, {longitude}...")

    # Run Pipeline
    result = coordinator.process_new_incident(
        image_path=image_path,
        latitude=latitude,
        longitude=longitude,
        disaster_type=disaster_type,
        incident_id=incident_id,
        triage_override=triage_override,
        audio_path=audio_path  # Pass audio path
    )
    
    # Print results in clean format
    print("\n" + "="*70)
    print("DAMAGE ASSESSMENT REPORT")
    print("="*70)
    
    # Print the report as clean text (not escaped JSON)
    report = result.get("damage_assessment_report", "No report available")
    print(report)
    
    # Apply Chat Log Override to Triage
    # Note: process_new_incident already called PostProcessor, but without the override.
    # We re-run the Triage calculation here for the final table display.
    if triage_override:
        print(f"\n[SYSTEM] Re-calculating priority based on {triage_override['panic_score']} PANIC signal...")
        processor = coordinator.agents["post_processor"]
        triage_final = processor._recommend_priority(
            result["patterns"].get("mode", "medium"), 
            1.5, 
            override=triage_override
        )
    else:
        triage_final = result.get("triage_priority_map", {})

    # Print metrics as table
    print("\n" + "="*70)
    print("ASSESSMENT METRICS (Fused with Distress Signals)")
    print("="*70)
    
    quality = result.get("quality_metrics", {})
    conf = result.get("confidence_score", 0)
    
    print(f'''
┌────────────────────────────────────────────────────────────────────┐
│  METRIC                          │  VALUE                         │
├──────────────────────────────────┼─────────────────────────────────┤
│  Incident ID                     │  {result.get('incident_id', 'N/A'):<30} │
│  Status                          │  {result.get('status', 'N/A'):<30} │
│  Disaster Type                   │  {result.get('disaster_type', 'N/A'):<30} │
│  Location                        │  {result.get('location', {}).get('latitude', 0):.4f}, {result.get('location', {}).get('longitude', 0):.4f}          │
├──────────────────────────────────┼─────────────────────────────────┤
│  Priority Level                  │  {triage_final.get('priority_level', 'N/A').upper():<30} │
│  Damage Severity                 │  {triage_final.get('damage_severity', 'N/A').upper():<30} │
│  Response Time                   │  {triage_final.get('response_time_hours', 'N/A')} hours{' '*24} │
│  Confidence Score                │  {conf*100:.1f}%{' '*27} │
├──────────────────────────────────┼─────────────────────────────────┤
│  Resource: Personnel             │  {triage_final.get('resource_allocation', {}).get('personnel', 0):<30} │
│  Resource: Vehicles              │  {triage_final.get('resource_allocation', {}).get('vehicles', 0):<30} │
│  Resource: Funds %               │  {triage_final.get('resource_allocation', {}).get('funds_percent', 0):<30} │
├──────────────────────────────────┼─────────────────────────────────┤
│  Quality Score                   │  {quality.get('quality_score', 0)*100:.1f}%{' '*26} │
│  Similar Incidents Found         │  {quality.get('result_count', 0):<30} │
└────────────────────────────────────────────────────────────────────┘
''')

def main():
    """Main entry point for CLI usage."""
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
        
        if "--batch-ingest" in sys.argv:
            print("\n" + "="*70)
            print("BATCH INGESTION MODE: Processing xBD Dataset")
            print("="*70 + "\n")
            coordinator.batch_ingest_xbd_data()
            
            print("\n" + "="*70)
            print("BATCH INGESTION: Audio Data")
            print("="*70 + "\n")
            ingest_audio_folder("audio_data")
        else:
            # Default to Rakshak Assessment
            run_rakshak_assessment(coordinator)
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
