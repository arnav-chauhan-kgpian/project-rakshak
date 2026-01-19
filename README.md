# Multi-Agent Disaster Response System (MAS)

A sophisticated 14-agent distributed system for real-time disaster damage assessment using satellite imagery and vector similarity search.

## System Architecture

### Overview
```
disaster/
├── main.py                          # Agent 14: Central Coordinator (Orchestrator)
├── requirements.txt                 # Dependencies
├── layers/
│   ├── ingestion/                  # LAYER 1: PERCEPTION (Agents 1-4)
│   │   ├── satellite.py            # Agent 1: Satellite imagery ingestion
│   │   ├── embedding.py            # Agent 2: DINOv2 feature extraction (768-dim)
│   │   ├── metadata.py             # Agent 3: JSON metadata parsing
│   │   └── qdrant_upsert.py        # Agent 4: Vector database storage
│   ├── search/                     # LAYER 2: RETRIEVAL (Agents 5-8)
│   │   ├── query_planner.py        # Agent 5: Query planning (spatial/temporal filters)
│   │   ├── hybrid_search.py        # Agent 6: Qdrant hybrid search (vector + metadata)
│   │   ├── cross_transfer.py       # Agent 7: Cross-disaster transfer learning
│   │   └── validator.py            # Agent 8: Result quality validation
│   └── reasoning/                  # LAYER 3: REASONING (Agents 9-13)
│       ├── synthesis.py            # Agent 9: Evidence pattern synthesis
│       ├── llm_reasoning.py        # Agent 10: Citation-based LLM reports
│       ├── confidence.py           # Agent 11: Confidence score calibration
│       ├── explanation.py          # Agent 12: Visual explanation package
│       └── priority.py             # Agent 13: Triage priority recommendation
└── utils/
    └── qdrant_init.py              # Collection initialization
```

## 14 Agents Breakdown

### Layer 1: Perception / Ingestion
1. **SatelliteAgent** - Downloads post-disaster satellite imagery from Maxar, Planet, or Sentinel-2
2. **EmbeddingAgent** - Extracts 768-dimensional DINOv2 embeddings from imagery
3. **MetadataAgent** - Parses and structures metadata (timestamp, geolocation, sensor info)
4. **QdrantUpsertAgent** - Stores embeddings and metadata in Qdrant vector database

### Layer 2: Retrieval / Search
5. **QueryPlannerAgent** - Plans search strategy with disaster-type-specific filters
   - Earthquake: 50km radius, 30-day window
   - Flood: 100km radius, 14-day window
   - Wildfire: 200km radius, 60-day window
   - Hurricane: 300km radius, 45-day window
6. **SearchExecutionAgent** - Hybrid search combining vector similarity + spatial/temporal metadata filters
7. **CrossDisasterAgent** - Cross-disaster transfer learning with penalty multipliers
8. **RelevanceValidatorAgent** - Validates result quality and confidence metrics

### Layer 3: Reasoning
9. **EvidenceSynthesisAgent** - Analyzes patterns and creates severity distribution histograms
10. **LLMReasoningAgent** - Generates grounded damage assessment reports with citations
11. **ConfidenceControllerAgent** - Calibrates confidence scores (60% vector similarity + 40% evidence quality)
12. **ExplanationAgent** - Generates visual explanation package (heatmaps, timelines, gauges)
13. **PriorityAgent** - Recommends triage priority levels (low/medium/high/critical) with resource allocation

### Layer 4: Orchestration
14. **CentralCoordinator** - Orchestrates all 13 agents through the complete pipeline

## Data Flow

```
New Disaster Incident
    ↓
[LAYER 1] PERCEPTION
    ↓
Satellite Image → DINOv2 Embedding → Metadata Parsing → Qdrant Storage
    ↓
[LAYER 2] RETRIEVAL
    ↓
Query Planning → Hybrid Search → Cross-Disaster Penalty → Validation
    ↓
[LAYER 3] REASONING
    ↓
Pattern Synthesis → LLM Report → Confidence Calibration → Visual Explanation → Priority
    ↓
[FINAL OUTPUT]
├── Damage Assessment Report (with citations)
├── Triage Priority Map (resource allocation)
├── Confidence Score (0-100%)
└── Visual Explanation Package (heatmaps, timelines)
```

## Key Technologies

- **Vector Database**: Qdrant (HNSW for efficient similarity search)
- **Embeddings**: DINOv2 (Vision Transformer) - 768-dimensional
- **Distance Metric**: Cosine similarity
- **Search Type**: Hybrid (vector + metadata filtering)
- **LLM Integration**: OpenAI API for grounded reports
- **Visualization**: Matplotlib for heatmaps and timelines

## Setup & Installation

### Prerequisites
- Python 3.9+
- Qdrant server running locally (port 6333)

### Installation

```bash
# Install Qdrant locally (Docker recommended)
docker run -p 6333:6333 qdrant/qdrant

# Clone and setup
cd disaster
pip install -r requirements.txt

# Initialize Qdrant collection
python utils/qdrant_init.py
```

## Usage

### Basic Example

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
    incident_id="EQ_2024_001"
)

# Access results
print(result["damage_assessment_report"])
print(result["triage_priority_map"])
print(f"Confidence: {result['confidence_score']:.2%}")
```

### Running the Complete Pipeline

```bash
python main.py
```

## Output Structure

```json
{
  "incident_id": "EarthQuake_LA_2024_001",
  "status": "COMPLETED",
  "location": {
    "latitude": 34.0522,
    "longitude": -118.2437
  },
  "disaster_type": "earthquake",
  "damage_assessment_report": "...",
  "triage_priority_map": {
    "priority_level": "high",
    "priority_score": 0.78,
    "response_time_hours": 6,
    "resource_allocation": {
      "personnel": 60,
      "vehicles": 15,
      "funds_percent": 35
    }
  },
  "confidence_score": 0.82,
  "explanation_package": {
    "severity_heatmap": {...},
    "timeline": {...},
    "confidence_visualization": {...}
  },
  "quality_metrics": {
    "result_count": 8,
    "avg_score": 0.75,
    "quality_score": 0.75
  }
}
```

## Agent Communication Protocol

Agents communicate through:
1. **Structured Data Dictionaries** - Standard Python dicts with typed payloads
2. **Qdrant API** - Vector database queries and storage
3. **Payload Metadata** - Qdrant point payloads carry incident metadata

## Configuration Parameters

### Query Planning Thresholds
- `spatial_radius_km`: Search radius by disaster type
- `temporal_days`: How far back to search for similar incidents
- `severity_threshold`: Minimum confidence for results
- `max_results`: Maximum number of results to retrieve

### Validation Rules
- `score_threshold`: 0.60 minimum for acceptance
- `required_results`: At least 3 similar incidents needed
- Automatic rejection if quality score < 0.60

### Confidence Calibration
- Vector similarity weight: 60%
- Evidence quality weight: 40%
- Base calibration: 0.7

## Performance Metrics

- **Vector Dimension**: 768 (DINOv2)
- **Search Type**: Hybrid (vector + filters)
- **Typical Latency**: ~200-500ms per incident
- **Memory**: ~2GB for embeddings (scales with incident count)

## Testing

The system includes mock implementations for:
- Satellite imagery ingestion (local file paths)
- DINOv2 embeddings (random normalized vectors)
- Metadata parsing (structured JSON)
- LLM reports (template-based)

For production:
1. Connect to real Maxar/Planet APIs
2. Replace mock embeddings with actual DINOv2 model
3. Integrate OpenAI API for LLM reports
4. Connect to real GIS/mapping systems

## Error Handling

All agents include:
- Try-except blocks with logging
- Graceful fallbacks
- Error status reporting
- Exception propagation to coordinator

## Future Enhancements

1. **Real-time Streaming**: WebSocket support for live satellite feeds
2. **Multi-Modal Analysis**: Radar + Optical + Thermal fusion
3. **Graph Analysis**: Incident relationship graphs
4. **Advanced LLM**: GPT-4 Vision for image understanding
5. **Mobile API**: REST endpoints for mobile clients
6. **Distributed Agents**: Multi-node deployment with message queues

## References

- Qdrant Documentation: https://qdrant.tech
- DINOv2: https://github.com/facebookresearch/dinov2
- Problem Statement: See `Qdrant - MAS PS Final - Convolve 4.0 - R2.pdf`

## License

Hackathon Project - Convolve 4.0

---

**Created**: January 2024
**Last Updated**: January 17, 2026
**Version**: 1.0
