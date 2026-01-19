# Multi-Agent Disaster Response System - Architecture Document

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 MULTI-AGENT DISASTER RESPONSE SYSTEM (MAS)                  │
│                      14 Agents | 3 Layers | 1 Coordinator                   │
└─────────────────────────────────────────────────────────────────────────────┘

                              INCIDENT INPUT
                         (Image + Geo + Disaster Type)
                                    │
                                    ▼
        ┌───────────────────────────────────────────────────────────┐
        │              LAYER 1: PERCEPTION/INGESTION                │
        │              Agents 1-4 (Acquisition Phase)               │
        ├───────────────────────────────────────────────────────────┤
        │                                                             │
        │  [Agent 1]        [Agent 2]       [Agent 3]   [Agent 4]   │
        │  Satellite    →   Embedding    →  Metadata  →  Qdrant    │
        │  Imagery         Extraction       Parsing      Upsert     │
        │  Download        (DINOv2)         (JSON)      (768-dim)   │
        │                  (768-dim)                                  │
        │                                                             │
        └────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
        ┌───────────────────────────────────────────────────────────┐
        │              LAYER 2: RETRIEVAL/SEARCH                    │
        │              Agents 5-8 (Search Phase)                    │
        ├───────────────────────────────────────────────────────────┤
        │                                                             │
        │  [Agent 5]      [Agent 6]        [Agent 7]    [Agent 8]   │
        │  Query      →   Hybrid      →    Cross-     →  Relevance │
        │  Planner        Search           Disaster       Validator │
        │  (Disaster      (Vector +        Transfer                  │
        │   Specific)     Metadata)        Learning                  │
        │                                  (Penalties)               │
        │                                                             │
        │         ◄────────────────────────────────────►            │
        │              QDRANT VECTOR DATABASE                       │
        │         (Stores all past incidents + embeddings)          │
        │                                                             │
        └────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
        ┌───────────────────────────────────────────────────────────┐
        │              LAYER 3: REASONING                           │
        │              Agents 9-13 (Analysis Phase)                 │
        ├───────────────────────────────────────────────────────────┤
        │                                                             │
        │  [Agent 9]     [Agent 10]    [Agent 11]    [Agent 12]    │
        │  Evidence   →   LLM      →   Confidence  →  Explanation  │
        │  Synthesis      Reasoning    Controller      Generator    │
        │  (Pattern      (Grounded    (Calibrate)    (Visuals)     │
        │   Analysis)     Reports)                                   │
        │                                                             │
        │                           ↓                                │
        │                      [Agent 13]                            │
        │                      Priority                              │
        │                      Agent                                 │
        │                      (Triage)                              │
        │                                                             │
        └────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
                            FINAL ASSESSMENT OUTPUT
                    ┌─────────────────────────────────┐
                    │ • Damage Assessment Report      │
                    │ • Triage Priority Map           │
                    │ • Confidence Score (0-100%)     │
                    │ • Visual Explanation Package    │
                    │ • Resource Allocation Plan      │
                    └─────────────────────────────────┘
```

## Detailed Agent Interactions

### Layer 1: Perception/Ingestion

```
┌─────────────────────────┐
│   Satellite Imagery     │
│    (GeoTIFF, TIF)       │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ Agent 1: SATELLITE AGENT                        │
│ • Download from Maxar/Planet/Sentinel-2 APIs   │
│ • Handle cloud cover & atmospheric conditions   │
│ • Manage AOI bounds (lat/lon)                   │
│ Output: List of image tiles + metadata         │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ Agent 2: EMBEDDING AGENT                        │
│ • Load satellite image                          │
│ • Preprocess: resize to 224x224                │
│ • Pass through DINOv2 Vision Transformer       │
│ • Output: 768-dimensional embedding vector     │
│ • Normalization: L2 norm                       │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ Agent 3: METADATA AGENT                         │
│ • Extract: timestamp, sensor info              │
│ • Parse: cloud_cover, resolution               │
│ • Structure: Schema v1.0 JSON                  │
│ • Geolocation: lat/lon bounds                  │
│ Output: Structured metadata dict               │
└────────────┬────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│ Agent 4: QDRANT UPSERT AGENT                    │
│ • Create PointStruct(id, vector, payload)      │
│ • Payload: incident_id, disaster_type, geoloc │
│ • Upsert to "disaster_memory" collection       │
│ • Dimension: 768, Distance: Cosine             │
│ Output: Storage confirmation + point ID        │
└─────────────────────────────────────────────────┘
```

### Layer 2: Retrieval/Search

```
┌──────────────────────────────────────────────────┐
│ Agent 5: QUERY PLANNER                           │
│                                                   │
│ Input: lat, lon, disaster_type                  │
│                                                   │
│ Disaster-specific strategies:                    │
│ • Earthquake: 50km radius, 30 days, 0.6 conf   │
│ • Flood: 100km radius, 14 days, 0.5 conf       │
│ • Wildfire: 200km radius, 60 days, 0.4 conf    │
│ • Hurricane: 300km radius, 45 days, 0.55 conf  │
│                                                   │
│ Output: Search plan with filters                │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│ Agent 6: SEARCH EXECUTION AGENT                  │
│                                                   │
│ • Build Qdrant Filter:                          │
│   - Disaster type match (FieldCondition)        │
│   - Spatial range (latitude ±delta)             │
│   - Longitude range (longitude ±delta)          │
│ • Execute hybrid search:                        │
│   - Vector similarity (query embedding)         │
│   - Apply metadata filters                      │
│   - Limit results (k=10)                        │
│ • Return: ScoredPoints with scores              │
│                                                   │
│ Output: List of similar incidents (id, score)   │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│ Agent 7: CROSS-DISASTER TRANSFER AGENT           │
│                                                   │
│ • For each result:                              │
│   - Check disaster_type in payload              │
│   - Apply similarity penalty:                   │
│     * Same type: 1.0x multiplier                │
│     * Similar: 0.7-0.9x multiplier              │
│     * Different: 0.5x multiplier                │
│   - Adjust score: new_score = old * penalty    │
│ • Re-sort by adjusted score                     │
│                                                   │
│ Output: Refined results with penalties applied  │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│ Agent 8: RELEVANCE VALIDATOR                     │
│                                                   │
│ • Calculate quality metrics:                    │
│   - Mean score, median, max                     │
│   - Variance, result count                      │
│ • Validation rules:                             │
│   - Threshold: avg_score >= 0.60                │
│   - Minimum results: count >= 3                 │
│ • Return status: ACCEPT | WARN | REJECT         │
│                                                   │
│ Output: (status, quality_metrics)               │
│         If REJECT → Early exit                  │
└──────────────────────────────────────────────────┘
```

### Layer 3: Reasoning

```
┌──────────────────────────────────────────────────┐
│ Agent 9: EVIDENCE SYNTHESIS AGENT                │
│                                                   │
│ • Extract damage_severity from results          │
│ • Create Counter histogram                      │
│ • Calculate mode severity                       │
│ • Geographic center (mean lat/lon)              │
│ • Temporal trend analysis                       │
│ • Confidence level (mean score)                 │
│                                                   │
│ Output: {mode, distribution, center, trend}    │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│ Agent 10: LLM REASONING AGENT                    │
│                                                   │
│ • Format evidence for context:                  │
│   - Incident ID & timestamp                     │
│   - Disaster type & location                    │
│   - Top-N similar incidents                     │
│ • Generate report template:                     │
│   - Severity assessment                         │
│   - Analysis narrative                          │
│   - Evidence citations [1] [2] [3]             │
│   - Confidence score                            │
│ • (Production: Call OpenAI API)                 │
│                                                   │
│ Output: Grounded damage assessment report       │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│ Agent 11: CONFIDENCE CALIBRATION                 │
│                                                   │
│ Calibration formula:                            │
│ conf = 0.6 * vector_score + 0.4 * evidence_q   │
│ calibrated = base_calib + (conf - 0.5) * factor│
│                                                   │
│ Range: [0.0, 1.0]                              │
│ Base calibration: 0.7                           │
│                                                   │
│ Output: Calibrated confidence score             │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│ Agent 12: EXPLANATION GENERATOR                  │
│                                                   │
│ • Create 4 visual components:                   │
│   1. Severity heatmap (spatial)                 │
│   2. Timeline chart (temporal trend)            │
│   3. Impact zones (geographic)                  │
│   4. Confidence gauge (confidence score)        │
│                                                   │
│ Output: Explanation package with URLs/data      │
└────────────┬─────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────┐
│ Agent 13: PRIORITY AGENT                         │
│                                                   │
│ Priority levels:                                │
│ • CRITICAL: 1h response, 100 personnel          │
│ • HIGH: 6h response, 60 personnel               │
│ • MEDIUM: 24h response, 30 personnel            │
│ • LOW: 72h response, 10 personnel               │
│                                                   │
│ Calculation:                                    │
│ priority = damage_level * confidence_factor    │
│ Clamp to [1, 4] → Map to level names           │
│                                                   │
│ Output: Priority level + resource allocation   │
└──────────────────────────────────────────────────┘
```

## Data Structures

### Incident Metadata
```python
metadata = {
    "schema_version": "1.0",
    "timestamp": "2024-01-17T12:30:00Z",
    "image_path": "imagery/tile_001.tif",
    "disaster_type": "earthquake",
    "geolocation": {
        "lat_min": 33.95, "lat_max": 34.15,
        "lon_min": -118.35, "lon_max": -118.15
    },
    "acquisition_date": "2024-01-17T12:00:00Z",
    "sensor_info": {
        "type": "Multispectral",
        "bands": 4,
        "resolution_cm": 15
    },
    "quality_metrics": {
        "cloud_cover_percent": 5.2,
        "atmospheric_opacity": 0.08,
        "signal_to_noise_ratio": 45.3
    }
}
```

### Search Result
```python
result = {
    "id": 1,
    "score": 0.85,  # Similarity score
    "original_score": 0.91,
    "penalty_factor": 0.93,  # Cross-disaster penalty
    "payload": {
        "incident_id": "EQ_2023_001",
        "disaster_type": "earthquake",
        "timestamp": "2023-11-15T08:45:00Z",
        "latitude": 34.05,
        "longitude": -118.24,
        "damage_severity": "high",
        "confidence_score": 0.85,
        "full_metadata": {...}
    }
}
```

### Final Output
```python
output = {
    "incident_id": "EQ_2024_001",
    "status": "COMPLETED",
    "location": {"latitude": 34.0522, "longitude": -118.2437},
    "disaster_type": "earthquake",
    "damage_assessment_report": "DAMAGE ASSESSMENT REPORT\n...",
    "triage_priority_map": {
        "priority_level": "high",
        "priority_score": 0.78,
        "damage_severity": "high",
        "confidence_adjusted": 1.5,
        "resource_allocation": {
            "personnel": 60,
            "vehicles": 15,
            "funds_percent": 35
        },
        "response_time_hours": 6,
        "triage_notes": "Recommended priority: HIGH - Damage: high, Confidence: 1.50x"
    },
    "confidence_score": 0.82,
    "explanation_package": {
        "report_summary": "...",
        "components": {
            "severity_heatmap": {...},
            "timeline": {...},
            "confidence_visualization": {...}
        },
        "metadata": {...}
    },
    "quality_metrics": {
        "result_count": 8,
        "avg_score": 0.75,
        "quality_score": 0.75
    }
}
```

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Vector DB | Qdrant | Store & search embeddings |
| Embeddings | DINOv2 (ViT) | 768-dim satellite image features |
| Search | HNSW | Fast nearest neighbor search |
| Distance | Cosine | Embedding similarity metric |
| LLM | OpenAI API | Generate grounded reports |
| Python | 3.9+ | Implementation language |
| Dependencies | torch, transformers, pillow | ML frameworks |

## Performance Characteristics

- **Embedding Extraction**: ~50-100ms per image
- **Vector Search**: ~10-50ms for k=10 results
- **Cross-Disaster Penalties**: ~1ms per result
- **Quality Validation**: ~5-10ms
- **LLM Report Generation**: ~1-3 seconds (API call)
- **Total Latency**: ~200-500ms per incident

## Error Handling Strategy

All agents implement:
1. Try-except blocks with logging
2. Graceful fallbacks (return empty/default values)
3. Exception propagation to coordinator
4. Status tracking (SUCCESS/WARN/ERROR)

---

**Document Version**: 1.0
**Last Updated**: January 2026
