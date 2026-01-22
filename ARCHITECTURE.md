# Project Rakshak: Complete System Architecture

> **15-Agent Multi-Modal Disaster Response Pipeline**  
> Built with Qdrant, Gemini 2.5 Flash, DINOv2, Whisper, CLAP  
> Made by Shaunak Majumdar and Arnav Chauhan, IIT Kharagpur

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Agent-by-Agent Breakdown](#agent-by-agent-breakdown)
3. [Data Flow Explanation](#data-flow-explanation)
4. [Feedback Loops & Guardrails](#feedback-loops--guardrails)
5. [Complete Mermaid Diagram](#complete-mermaid-diagram)

---

## System Overview

Project Rakshak consists of **two parallel pipelines** that can operate independently or together:

| Pipeline | Purpose | Entry Point | Output |
|----------|---------|-------------|--------|
| **Distress Signal Pipeline** | Real-time emergency chat with victims | Voice/Text input from `app.py` | Triage JSON with priority |
| **Rakshak Intel Pipeline** | Satellite imagery analysis | Image + GPS from `main.py` | Emergency Report + Visualizations |

Both pipelines share:
- **Qdrant Vector Database** (disaster_memory, disaster_audio collections)
- **Gemini 2.5 Flash LLM** (for reasoning and chat)
- **Common Guardrails** (PII scrubbing, retry logic, input validation)

---

## Agent-by-Agent Breakdown

### DISTRESS SIGNAL PIPELINE (Chat Mode)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DISTRESS SIGNAL PIPELINE                     │
│   Entry: Voice/Text Input → Exit: Triage Report                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Step D1: Voice Input Processing
**File:** `utils/voice_input.py`

| Component | Technology | Function |
|-----------|------------|----------|
| **Whisper STT** | `openai/whisper-tiny` | Converts audio → text transcript |
| **CLAP Audio** | `laion/clap-htsat-unfused` | Generates 512-dim audio embeddings for panic detection |

**Data Flow:**
```
Audio (WAV) → Whisper → Transcript (Text)
           ↘ CLAP → Audio Embedding (512-dim) → Panic Score
```

#### Step D2: VictimChatAgent
**File:** `layers/reasoning/victim_chat.py`

| Component | Technology | Function |
|-----------|------------|----------|
| **Chat LLM** | `Gemini 2.5 Flash` | Multi-turn conversational AI with emergency context |
| **PII Scrubber** | Regex patterns | Removes names, phone numbers, addresses before LLM |
| **Panic Analyzer** | Rule-based + CLAP | Detects urgency from voice tremor/keywords |

**Internal Loop (Multi-turn Conversation):**
```
User Message → PII Scrubber → Gemini LLM → Response
     ↑                                         │
     └─────────── Continue Chat ───────────────┘
```

**Session Analysis Flow:**
```
Chat History → analyze_session() → Triage JSON {
    "priority": "HIGH",
    "resources_needed": ["Ambulance", "Fire"],
    "eta": "15 minutes",
    "key_details": {...}
}
```

#### Step D3: Triage Override Connection
**Connection to Main Pipeline:**
```
Triage JSON ─────────────→ PostProcessorAgent (Panic Boost)
             "priority"       Increases resource allocation
```

---

### RAKSHAK INTEL PIPELINE (14 Agents)

```
┌─────────────────────────────────────────────────────────────────┐
│                    RAKSHAK INTEL PIPELINE                        │
│   Entry: Satellite Image + GPS → Exit: Emergency Report         │
└─────────────────────────────────────────────────────────────────┘
```

#### LAYER 1: PERCEPTION (Agents 1-5)

##### Agent 1: SatelliteAgent
**File:** `layers/ingestion/satellite.py`

| Input | Process | Output |
|-------|---------|--------|
| Image path (PNG/JPG) | Validates format, resolution, file existence | PIL Image object |

**Guardrail:** Input Validation (rejects corrupted/invalid images)

```
image_path → validate_image() → PIL.Image
                ↓
           [REJECT if invalid]
```

##### Agent 2: EmbeddingAgent
**File:** `layers/ingestion/embedding.py`

| Input | Process | Output |
|-------|---------|--------|
| PIL Image | DINOv2 ViT-B/14 forward pass | 768-dim dense vector |

**Thread Safety:** Model loading protected by mutex lock

```
PIL.Image → Resize(224x224) → DINOv2 → Dense Vector [768-dim]
```

##### Agent 3: SparseEmbeddingAgent
**File:** `layers/ingestion/sparse_embedding.py`

| Input | Process | Output |
|-------|---------|--------|
| Metadata (disaster_type, location) | BM25 tokenization | Sparse vector (indices + values) |

```
"earthquake, Los Angeles, 34.05, -118.24" → BM25 → Sparse Vector
```

##### Agent 4: MetadataAgent
**File:** `layers/ingestion/metadata.py`

| Input | Process | Output |
|-------|---------|--------|
| Image path + GPS | Extracts EXIF, formats payload | Metadata dict |

```
{image_path, lat, lon, disaster_type} → metadata dict {
    "incident_id": "...",
    "location": {"lat": 34.05, "lon": -118.24},
    "disaster_type": "earthquake",
    "timestamp": "2024-01-22T..."
}
```

##### Agent 5: QdrantUpsertAgent
**File:** `layers/ingestion/qdrant_upsert.py`

| Input | Process | Output |
|-------|---------|--------|
| Dense + Sparse vectors, Metadata | Upsert to Qdrant | Point ID |

```
{dense_vector, sparse_vector, metadata} → Qdrant.upsert() → point_id
                                              ↓
                                    [disaster_memory collection]
```

---

#### LAYER 2: RETRIEVAL (Agents 6-8)

##### Agent 6: SearchProcessorAgent
**File:** `layers/search/search_processor.py`

| Input | Process | Output |
|-------|---------|--------|
| Query image + metadata | Builds hybrid search configuration | Search params |

**Merged Functionality:** Combines query building, filter construction, and ranking config

```
{disaster_type, location} → SearchParams {
    "dense_weight": 0.7,
    "sparse_weight": 0.3,
    "filters": {"disaster_type": ["earthquake", "flood"]},
    "limit": 10
}
```

##### Agent 7: SearchExecutionAgent
**File:** `layers/search/hybrid_search.py`

| Input | Process | Output |
|-------|---------|--------|
| Query vectors + SearchParams | Hybrid RRF Search on Qdrant | Ranked results |

**Key Feature:** Binary Quantization with 2x oversampling + rescore

```
Query Vectors → Qdrant.query_points() → RRF Fusion → Top-K Results
                     ↓                      ↓
              [Binary Quantization]    [Rescore with full vectors]
                  (40x faster)
```

##### Agent 8: GeoSimilarityAgent
**File:** `layers/reasoning/geo_search.py`

| Input | Process | Output |
|-------|---------|--------|
| GPS coordinates | Geo-filtered search within radius | Nearby incidents |

```
{lat, lon, radius_km} → Geo-Filter → Nearby Historical Incidents [
    {"id": "INC_001", "distance_km": 2.5, "damage": "major"},
    ...
]
```

---

#### LAYER 3: REASONING (Agents 9-14)

##### Agent 9: EvidenceSynthesisAgent
**File:** `layers/reasoning/recomm.py`

| Input | Process | Output |
|-------|---------|--------|
| Search results | Pattern extraction + aggregation | Patterns dict |

```
Search Results → Aggregate Damage Types → Patterns {
    "damage_counts": {"destroyed": 5, "major-damage": 8, ...},
    "severity_distribution": {"critical": 0.3, "high": 0.5, ...},
    "mode": "high",
    "geographic_center": [34.05, -118.24],
    "quality_score": 0.78
}
```

##### Agent 10: HistorySummarizerAgent
**File:** `layers/reasoning/history_summarizer.py`

| Input | Process | Output |
|-------|---------|--------|
| Nearby incidents | Narrative generation | Context paragraph |

```
Nearby Incidents → Generate Summary → "Historical context: This region 
experienced 3 major floods in the past decade. The 2020 disaster 
resulted in 50+ casualties..."
```

##### Agent 11: LLMReasoningAgent (CORE)
**File:** `layers/reasoning/llm_reasoning.py`

| Input | Process | Output |
|-------|---------|--------|
| Patterns + History + Metadata | Gemini 2.5 Flash prompt | Draft Report |

**Guardrail:** Exponential backoff retry (3 attempts, 2x delay)

```
{patterns, history_summary, metadata} → Prompt Template → Gemini API
                                            ↓
                                    Draft Report (Markdown)
```

##### Agent 12: ReportAuditorAgent (VERIFIER)
**File:** `layers/reasoning/evaluator.py`

| Input | Process | Output |
|-------|---------|--------|
| Draft Report + Metadata | Fact-checking LLM pass | Verified Report |

**FEEDBACK LOOP:** Auditor can request corrections from LLM

```
Draft Report → Auditor Prompt → Gemini API → {
    "verified": true/false,
    "corrections": [...],
    "final_report": "..."
}
        ↓
   [If corrections needed]
        ↓
   Re-submit to Agent 11 (LLMReasoningAgent)
```

##### Agent 13: PostProcessorAgent
**File:** `layers/reasoning/post_processor.py`

| Input | Process | Output |
|-------|---------|--------|
| Verified Report + Patterns + Triage Override | Confidence + Priority | Final metadata |

**Merged Agents:** Combines Confidence (11), Explanation (12), Priority (13)

```
{report, patterns, quality_metrics, triage_override} → 
    _calculate_confidence() → confidence_score (0.0-1.0)
    _recommend_priority() → triage {
        "priority_level": "critical",
        "response_time_hours": 1,
        "resource_allocation": {"personnel": 80, "vehicles": 20}
    }
```

**Triage Override (from Chatbot):**
```
If triage_override.panic_score == "High":
    priority_level += 1 tier (e.g., "high" → "critical")
```

##### Agent 14: ExplanationAgent (VISUALIZATION)
**File:** `layers/reasoning/explanation.py`

| Input | Process | Output |
|-------|---------|--------|
| Report + Patterns + Confidence | Matplotlib chart generation | PNG paths |

**Charts Generated:**
1. `*_damage_distribution.png` - Bar chart of damage types
2. `*_confidence_gauge.png` - Half-circle gauge
3. `*_severity_breakdown.png` - Pie chart
4. `*_risk_radar.png` - 5-axis spider chart
5. `*_resource_allocation.png` - Horizontal bar chart

```
{patterns, confidence} → Matplotlib → 5 PNG files in reports/visualizations/
```

---

#### ORCHESTRATOR

##### Agent 15: CentralCoordinator
**File:** `main.py`

| Role | Function |
|------|----------|
| **Orchestrator** | Sequences all 14 agents in correct order |
| **Error Handler** | Catches exceptions, returns structured error |
| **Parallel Execution** | Runs SearchExecution + GeoSimilarity in parallel threads |

```python
def process_new_incident(image_path, lat, lon, disaster_type, ...):
    # LAYER 1
    image = agents["satellite"].validate(image_path)
    dense = agents["embedder"].embed(image)
    sparse = agents["sparse_embedder"].embed(metadata)
    agents["upsert"].store(dense, sparse, metadata)
    
    # LAYER 2 (Parallel)
    with ThreadPoolExecutor:
        results = agents["searcher"].search(...)
        nearby = agents["geo_search"].find_nearby(...)
    
    # LAYER 3
    patterns = agents["synthesizer"].analyze(results)
    history = agents["history_summarizer"].summarize(nearby)
    draft = agents["llm"].generate_report(patterns, history)
    verified = agents["auditor"].audit(draft)  # ← FEEDBACK LOOP
    final = agents["post_processor"].process(verified, patterns)
    charts = agents["explanation"].generate(final)
    
    return {report, charts, confidence, triage}
```

---

## Data Flow Explanation

### Complete Pipeline Flow (Numbered Steps)

```
[1] Input: Satellite Image + GPS Coordinates
        ↓
[2] SatelliteAgent validates image format
        ↓
[3] PARALLEL:
    ├─→ EmbeddingAgent → 768-dim dense vector
    └─→ SparseEmbeddingAgent → BM25 sparse vector
        ↓
[4] MetadataAgent extracts incident metadata
        ↓
[5] QdrantUpsertAgent stores to disaster_memory collection
        ↓
[6] SearchProcessorAgent builds hybrid query
        ↓
[7] PARALLEL:
    ├─→ SearchExecutionAgent → RRF-fused results (10 similar incidents)
    └─→ GeoSimilarityAgent → Nearby historical events (within 50km)
        ↓
[8] EvidenceSynthesisAgent aggregates damage patterns
        ↓
[9] HistorySummarizerAgent generates context narrative
        ↓
[10] LLMReasoningAgent (Gemini) generates draft report
        ↓
[11] ReportAuditorAgent fact-checks and corrects
        ↓ ←──── FEEDBACK LOOP (if corrections needed)
[12] PostProcessorAgent calculates confidence + priority
        ↓
        ├─→ If triage_override from Chatbot: boost priority
        ↓
[13] ExplanationAgent generates 5 visualization charts
        ↓
[14] FINAL OUTPUT: Emergency Report + Charts + Triage
```

---

## Feedback Loops & Guardrails

### Loop 1: Auditor Feedback Loop
```
LLMReasoningAgent ─────→ Draft Report ─────→ ReportAuditorAgent
       ↑                                            │
       │                                            ▼
       └──────── Re-generate with corrections ◄────┘
                    (max 2 iterations)
```

### Loop 2: Multi-Turn Chat Loop
```
User Message ────→ VictimChatAgent ────→ Response
      ↑                                      │
      └────────── Continue Conversation ◄────┘
```

### Loop 3: Retry Loop (API Calls)
```
Gemini API Call ────→ Success? ────→ Return Result
       ↑                  │
       │                  ▼ (Failure)
       └──── Wait (2^n seconds) ◄────┘
              (max 3 retries)
```

### Guardrails Summary

| Guardrail | Location | Trigger | Action |
|-----------|----------|---------|--------|
| **Input Validation** | SatelliteAgent | Invalid image | Return REJECTED status |
| **PII Scrubber** | VictimChatAgent | User message contains PII | Redact before LLM |
| **Exponential Backoff** | LLM Agents | API rate limit / error | Retry with 2^n delay |
| **Thread Safety** | EmbeddingAgent | Concurrent model access | Mutex lock |
| **Auditor Loop** | ReportAuditorAgent | Factual errors detected | Re-generate report |

---

## Complete Mermaid Diagram

```mermaid
flowchart TB
    subgraph INPUTS["🌐 INPUT SOURCES"]
        direction LR
        SAT_IMG["🛰️ Satellite Imagery<br/>(Sentinel-2 / Maxar)"]
        VOICE_IN["🎙️ Voice Input<br/>(Distress Call)"]
        TEXT_IN["💬 Text Chat<br/>(Emergency Message)"]
        GPS_IN["📍 GPS Coordinates<br/>(Lat/Lon)"]
    end

    subgraph DISTRESS_PIPELINE["🆘 DISTRESS SIGNAL PIPELINE"]
        direction TB
        
        subgraph VOICE_PROC["Voice Processing"]
            WHISPER["🎧 Whisper STT<br/>(whisper-tiny)"]
            CLAP["🔊 CLAP Audio<br/>(Panic Detection)"]
        end
        
        subgraph CHAT_AGENT["VictimChatAgent"]
            CHAT_LLM["🤖 Gemini 2.5 Flash<br/>(Conversational AI)"]
            PII_GUARD["🛡️ PII Scrubber<br/>(Guardrail)"]
            PANIC_ANALYZER["📊 Panic Analyzer<br/>(Sentiment)"]
        end
        
        TRIAGE_OUT["📋 Triage Report<br/>(JSON)"]
    end

    subgraph MAIN_PIPELINE["🛰️ RAKSHAK INTEL PIPELINE (14 Agents)"]
        direction TB
        
        subgraph LAYER1["LAYER 1: PERCEPTION"]
            A1["Agent 1: SatelliteAgent<br/>(Image Validation)"]
            A2["Agent 2: EmbeddingAgent<br/>(DINOv2 768-dim)"]
            A3["Agent 3: SparseEmbeddingAgent<br/>(BM25 Keywords)"]
            A4["Agent 4: MetadataAgent<br/>(EXIF + Geo)"]
            A5["Agent 5: QdrantUpsertAgent<br/>(Vector Storage)"]
        end

        subgraph LAYER2["LAYER 2: RETRIEVAL"]
            A6["Agent 6: SearchProcessorAgent<br/>(Query Builder)"]
            A7["Agent 7: SearchExecutionAgent<br/>(Hybrid RRF Search)"]
            A8["Agent 8: GeoSimilarityAgent<br/>(Spatial Context)"]
        end

        subgraph LAYER3["LAYER 3: REASONING"]
            A9["Agent 9: EvidenceSynthesisAgent<br/>(Pattern Analysis)"]
            A10["Agent 10: HistorySummarizerAgent<br/>(Context Narrative)"]
            A11["Agent 11: LLMReasoningAgent<br/>(Gemini 2.5 Flash)"]
            A12["Agent 12: ReportAuditorAgent<br/>(Fact-Check LLM)"]
            A13["Agent 13: PostProcessorAgent<br/>(Confidence + Triage)"]
            A14["Agent 14: ExplanationAgent<br/>(Visualization)"]
        end
    end

    subgraph QDRANT_DB["💾 QDRANT VECTOR DATABASE"]
        direction LR
        COLL_MAIN["disaster_memory<br/>(768-dim Dense + Sparse)"]
        COLL_AUDIO["disaster_audio<br/>(512-dim CLAP)"]
        BQ["⚡ Binary Quantization<br/>(40x Speed)"]
    end

    subgraph GUARDRAILS["🛡️ SYSTEM GUARDRAILS"]
        direction LR
        RETRY["🔄 Exponential Backoff<br/>(API Retry)"]
        THREAD_SAFE["🧵 Thread Safety<br/>(Model Locks)"]
        VALIDATION["✅ Input Validation<br/>(Image/Audio)"]
        AUDITOR_LOOP["🔁 Auditor Feedback Loop<br/>(LLM Self-Correction)"]
    end

    subgraph OUTPUTS["📊 OUTPUT LAYER"]
        direction LR
        REPORT["📄 Emergency Report<br/>(Markdown)"]
        CHARTS["📊 Visualization Charts<br/>(5 PNG Graphs)"]
        UI["🖥️ Streamlit Dashboard<br/>(app.py)"]
    end

    subgraph COORDINATOR["👑 CENTRAL COORDINATOR"]
        A15["Agent 15: CentralCoordinator<br/>(Orchestrator)"]
    end

    %% ========== CONNECTIONS ==========

    %% Inputs to Pipelines
    SAT_IMG --> A1
    GPS_IN --> A4
    VOICE_IN --> WHISPER
    VOICE_IN --> CLAP
    TEXT_IN --> CHAT_LLM

    %% Distress Pipeline Flow
    WHISPER --> CHAT_LLM
    CLAP --> PANIC_ANALYZER
    PANIC_ANALYZER --> CHAT_LLM
    CHAT_LLM --> PII_GUARD
    PII_GUARD --> TRIAGE_OUT

    %% Distress -> Main Pipeline (Triage Override)
    TRIAGE_OUT -.->|"Panic Override"| A13

    %% Layer 1 Flow
    A1 --> A2
    A1 --> A3
    A1 --> A4
    A2 --> A5
    A3 --> A5
    A4 --> A5

    %% Storage
    A5 --> COLL_MAIN
    CLAP --> COLL_AUDIO

    %% Layer 2 Flow
    A5 --> A6
    A6 --> A7
    COLL_MAIN --> A7
    BQ --> A7
    A7 --> A8

    %% Layer 3 Flow
    A8 --> A9
    A9 --> A10
    A9 --> A11
    A10 --> A11
    A11 --> A12
    A12 -.->|"Feedback Loop"| A11
    A12 --> A13
    A13 --> A14

    %% Guardrails Integration
    RETRY -.-> A11
    RETRY -.-> A12
    THREAD_SAFE -.-> A2
    VALIDATION -.-> A1
    AUDITOR_LOOP -.-> A12

    %% Coordinator Orchestration
    A15 --> LAYER1
    A15 --> LAYER2
    A15 --> LAYER3

    %% Outputs
    A14 --> CHARTS
    A12 --> REPORT
    CHARTS --> UI
    REPORT --> UI

    %% Styling
    classDef inputStyle fill:#3498db,stroke:#2980b9,color:white
    classDef distressStyle fill:#e74c3c,stroke:#c0392b,color:white
    classDef layer1Style fill:#1abc9c,stroke:#16a085,color:white
    classDef layer2Style fill:#9b59b6,stroke:#8e44ad,color:white
    classDef layer3Style fill:#e67e22,stroke:#d35400,color:white
    classDef dbStyle fill:#2c3e50,stroke:#1a252f,color:white
    classDef guardStyle fill:#f1c40f,stroke:#f39c12,color:black
    classDef outputStyle fill:#27ae60,stroke:#1e8449,color:white
    classDef coordStyle fill:#e94560,stroke:#c23b51,color:white

    class SAT_IMG,VOICE_IN,TEXT_IN,GPS_IN inputStyle
    class WHISPER,CLAP,CHAT_LLM,PII_GUARD,PANIC_ANALYZER,TRIAGE_OUT distressStyle
    class A1,A2,A3,A4,A5 layer1Style
    class A6,A7,A8 layer2Style
    class A9,A10,A11,A12,A13,A14 layer3Style
    class COLL_MAIN,COLL_AUDIO,BQ dbStyle
    class RETRY,THREAD_SAFE,VALIDATION,AUDITOR_LOOP guardStyle
    class REPORT,CHARTS,UI outputStyle
    class A15 coordStyle
```

---

## How to Draw the State Diagram

Using the information above, draw your state diagram with these steps:

1. **Start with Input nodes** (Satellite Image, Voice, Text, GPS) on the left
2. **Draw two parallel tracks**:
   - Upper: Distress Signal Pipeline (voice processing → chat → triage)
   - Lower: Rakshak Intel Pipeline (Layer 1 → Layer 2 → Layer 3)
3. **Connect the Qdrant database** in the center (both pipelines access it)
4. **Add the Feedback Loops**:
   - Dashed line from Auditor back to LLM
   - Dashed line from Triage to PostProcessor (panic override)
5. **Draw Guardrails** as separate boxes with dashed connections to their agents
6. **End with Output nodes** (Report, Charts, Dashboard) on the right

---

> **Made by Shaunak Majumdar and Arnav Chauhan, IIT Kharagpur**
