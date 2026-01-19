# Multi-Agent Disaster Response System - Quick Start Guide

## Installation (3 steps)

```bash
# 1. Start Qdrant server
docker run -p 6333:6333 qdrant/qdrant

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize Qdrant collection
python utils/qdrant_init.py
```

## Running the System

```bash
# Run complete demo
python main.py

# Use in Python
from main import CentralCoordinator
coordinator = CentralCoordinator()
result = coordinator.process_new_incident("image.png", 34.05, -118.24, "earthquake")
```

## 14 Agents at a Glance

| Layer | Agent # | Name | Purpose |
|-------|---------|------|---------|
| **Ingestion** | 1 | SatelliteAgent | Download imagery |
| | 2 | EmbeddingAgent | Extract 768-dim vectors |
| | 3 | MetadataAgent | Parse metadata JSON |
| | 4 | QdrantUpsertAgent | Store in Qdrant |
| **Retrieval** | 5 | QueryPlannerAgent | Plan search strategy |
| | 6 | SearchExecutionAgent | Hybrid vector+metadata search |
| | 7 | CrossDisasterAgent | Apply transfer learning penalties |
| | 8 | RelevanceValidatorAgent | Validate result quality |
| **Reasoning** | 9 | EvidenceSynthesisAgent | Pattern analysis & histograms |
| | 10 | LLMReasoningAgent | Generate grounded reports |
| | 11 | ConfidenceControllerAgent | Calibrate confidence scores |
| | 12 | ExplanationAgent | Create visual explanations |
| | 13 | PriorityAgent | Recommend triage priority |
| **Orchestration** | 14 | CentralCoordinator | Orchestrate all agents |

## Example Output

```
LAYER 1: PERCEPTION
  ✓ Satellite imagery ingestion
  ✓ 768-dimensional embedding extraction
  ✓ Metadata JSON parsing
  ✓ Vector database storage

LAYER 2: RETRIEVAL
  ✓ Query planning (50km radius, 30-day window)
  ✓ Hybrid search (8 similar incidents found)
  ✓ Cross-disaster penalties applied
  ✓ Quality validation: ACCEPT (score: 0.75)

LAYER 3: REASONING
  ✓ Pattern synthesis (mode: HIGH damage)
  ✓ LLM damage assessment report
  ✓ Confidence calibration: 82%
  ✓ Visual explanation package
  ✓ Triage priority: HIGH (6-hour response)

ASSESSMENT COMPLETE
```

## Key Configuration

### Search Parameters (by disaster type)
```python
"earthquake": {
    "spatial_radius_km": 50,
    "temporal_days": 30,
    "severity_threshold": 0.6
},
"flood": {
    "spatial_radius_km": 100,
    "temporal_days": 14,
    "severity_threshold": 0.5
},
"wildfire": {
    "spatial_radius_km": 200,
    "temporal_days": 60,
    "severity_threshold": 0.4
},
"hurricane": {
    "spatial_radius_km": 300,
    "temporal_days": 45,
    "severity_threshold": 0.55
}
```

### Priority Levels
- **CRITICAL**: 1-hour response | 100 personnel | 30 vehicles | 100% budget
- **HIGH**: 6-hour response | 60 personnel | 15 vehicles | 35% budget
- **MEDIUM**: 24-hour response | 30 personnel | 6 vehicles | 15% budget
- **LOW**: 72-hour response | 10 personnel | 2 vehicles | 5% budget

## Vector Database (Qdrant)

- **Collection**: `disaster_memory`
- **Vector Size**: 768 dimensions
- **Distance Metric**: Cosine similarity
- **Payload Fields**:
  - `incident_id`: Unique identifier
  - `disaster_type`: Disaster classification
  - `timestamp`: Event time
  - `latitude/longitude`: Geographic coordinates
  - `damage_severity`: Damage level
  - `confidence_score`: Model confidence
  - `full_metadata`: Complete metadata JSON

## Workflow Summary

```
INPUT: Satellite image + Location + Disaster type
   ↓
LAYER 1: Extract embedding → Store in Qdrant
   ↓
LAYER 2: Find similar incidents → Validate quality
   ↓
LAYER 3: Analyze patterns → Generate report → Assess priority
   ↓
OUTPUT: Report + Priority + Confidence + Explanation
```

## API Example

```python
from main import CentralCoordinator

# Initialize
coordinator = CentralCoordinator()

# Process incident
result = coordinator.process_new_incident(
    image_path="path/to/satellite_image.png",
    latitude=34.0522,
    longitude=-118.2437,
    disaster_type="earthquake",
    incident_id="EQ_LA_001"
)

# Access results
print(result["damage_assessment_report"])          # Grounded report with citations
print(result["triage_priority_map"])               # Priority & resource allocation
print(f"Confidence: {result['confidence_score']}")  # 0-1 score
print(result["explanation_package"])                # Visual components
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Qdrant connection error | `docker run -p 6333:6333 qdrant/qdrant` |
| Import errors | `pip install -r requirements.txt` |
| Collection not found | `python utils/qdrant_init.py` |
| Slow search | Add spatial filters in QueryPlannerAgent |
| Low confidence | Increase incident count in Qdrant |

## File Structure

```
disaster/
├── main.py                        # Main orchestrator (Agent 14)
├── requirements.txt               # Dependencies
├── README.md                      # Full documentation
├── QUICKSTART.md                  # This file
├── layers/
│   ├── ingestion/                # Agents 1-4
│   │   ├── satellite.py
│   │   ├── embedding.py
│   │   ├── metadata.py
│   │   └── qdrant_upsert.py
│   ├── search/                   # Agents 5-8
│   │   ├── query_planner.py
│   │   ├── hybrid_search.py
│   │   ├── cross_transfer.py
│   │   └── validator.py
│   └── reasoning/                # Agents 9-13
│       ├── synthesis.py
│       ├── llm_reasoning.py
│       ├── confidence.py
│       ├── explanation.py
│       └── priority.py
└── utils/
    └── qdrant_init.py            # Collection setup
```

## Performance Notes

- **Latency**: ~200-500ms per incident
- **Memory**: ~2GB for 10,000 incidents
- **Scalability**: Qdrant handles millions of vectors
- **Embeddings**: 768 dimensions = ~3KB per incident

## Support

For issues or questions:
1. Check README.md for detailed documentation
2. Review agent docstrings in source code
3. Check Qdrant logs: `docker logs <container_id>`
4. Verify Qdrant status: `http://localhost:6333/health`

---

**Version**: 1.0 | **Last Updated**: January 2026
