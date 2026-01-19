# Multi-Agent System Pipeline State Diagram & Analysis

## Current Problem: 0 Results from Search (REJECTED Status)

```
ROOT CAUSE: Schema Mismatch
┌─────────────────────────────────────────────────────┐
│ Collection Schema: Unnamed dense vector (OLD)       │
│ Expected Schema: Named vectors "image" + "text"     │
│ Result: Search fails to find vectors → 0 results    │
└─────────────────────────────────────────────────────┘
```

## System State Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                     SYSTEM INITIALIZATION                         │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ initialize_qdrant()│
                    └──────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
           Collection                  Collection
            EXISTS?                    NOT EXISTS
                │                           │
                ▼                           ▼
        ┌──────────────┐          ┌──────────────────┐
        │ Check Schema │          │ Create Collection │
        │  Compatibility│          │  Named Vectors   │
        └──────────────┘          │  - image (dense) │
                │                 │  - text (sparse) │
     ┌──────────┴──────────┐     └──────────────────┘
     │                     │
  Schema OK          Schema MISMATCH        
     │                     │                 
     ▼                     ▼                 
  PRESERVE          AUTO-RECREATE ✓ (FIX)
  Continue          Drop + Create
                    └─────────┬─────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                   AGENT INITIALIZATION                            │
│  CentralCoordinator() → All 14 agents initialized                │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      LAYER 1: PERCEPTION                          │
└──────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌──────────┐         ┌──────────┐
   │ Agent 1 │          │ Agent 2  │         │ Agent 3  │
   │Satellite│          │Embedding │         │Metadata  │
   │Imagery  │          │DINOv2    │         │Parser    │
   └─────────┘          │768-dim   │         │JSON+xBD  │
        │               └──────────┘         └──────────┘
        │                     │                     │
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                        ┌──────────┐
                        │ Agent 2b │
                        │  Sparse  │
                        │  BM25    │
                        └──────────┘
                              │
                              ▼
                        ┌──────────┐
                        │ Agent 4  │
                        │  Upsert  │────► Named Vectors?
                        └──────────┘          │
                              │         ┌─────┴─────┐
                              │         │           │
                              │       YES          NO
                              │         │           │
                              │    Use Named   Use Unnamed
                              │    (CORRECT)   (FALLBACK)
                              │         │           │
                              │         └─────┬─────┘
                              ▼               │
┌──────────────────────────────────────────────────────────────────┐
│                      LAYER 2: RETRIEVAL                           │
└──────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌──────────┐         ┌──────────┐
   │ Agent 5 │          │ Agent 6  │         │ Agent 7  │
   │  Query  │          │ Hybrid   │         │  Cross-  │
   │ Planner │          │ Search   │         │ Disaster │
   └─────────┘          └──────────┘         │ Transfer │
        │                     │               └──────────┘
        │                     │                     │
        │  Spatial Filter     │  Dense + Sparse     │
        │  Disaster Type      │  Self-Exclusion     │
        │  Radius: 50km       │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Search Process   │
                    └──────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
         Has Named                      Has Unnamed
         Vectors?                       Vectors?
              │                               │
          ┌───┴───┐                       ┌───┴───┐
          │       │                       │       │
         YES     NO                      YES     NO
          │       │                       │       │
     Try search   │                  Fallback    Empty
     with filters │                  Python      Result
          │       │                  Scroll      │
          │       │                  Cosine      │
          │       │                       │      │
          └───┬───┘                       └──┬───┘
              │                              │
              └──────────┬───────────────────┘
                         │
                    Results > 0?
                         │
              ┌──────────┴──────────┐
              │                     │
            YES                    NO
              │                     │
              ▼                     ▼
     ┌──────────────┐      ┌──────────────┐
     │  Continue    │      │   REJECT     │
     │  Pipeline    │      │  Status: 0   │
     └──────────────┘      │   results    │
              │             └──────────────┘
              ▼                     │
        ┌──────────┐               │
        │ Agent 8  │               │
        │Validator │               │
        └──────────┘               │
              │                    │
              ▼                    │
       ACCEPT/WARN                 │
              │                    │
              ▼                    ▼
┌──────────────────────────────────────────────────────────────────┐
│                      LAYER 3: REASONING                           │
│  (Only executes if validation passes)                            │
└──────────────────────────────────────────────────────────────────┘
              │
    ┌─────────┼─────────────────────┐
    │         │                     │
    ▼         ▼                     ▼
┌──────┐ ┌──────┐              ┌──────┐
│Agent9│ │Agent │              │Agent │
│Synth │ │ 10   │  ... →  ... │  13  │
│      │ │ LLM  │              │Prior.│
└──────┘ └──────┘              └──────┘
    │         │                     │
    └─────────┼─────────────────────┘
              ▼
        ┌──────────┐
        │  FINAL   │
        │  OUTPUT  │
        └──────────┘
```

## Problem Flow - Why 0 Results?

```
1. Qdrant Init
   ├─ Checks if collection exists → YES (933 points)
   ├─ Should check schema compatibility → ❌ NOT WORKING
   └─ Preserves old unnamed schema → ❌ WRONG

2. Upsert (Agent 4)
   ├─ Detects unnamed schema
   ├─ Falls back to unnamed vector upsert
   └─ ✓ Upsert succeeds (but wrong schema)

3. Search (Agent 6)
   ├─ Tries to search with named vector "image"
   ├─ Collection only has unnamed vectors
   ├─ Search returns empty
   └─ ❌ 0 results → REJECT

4. Validator (Agent 8)
   ├─ Receives 0 results
   └─ ❌ Status: REJECT → Pipeline exits
```

## Fix Strategy

### Immediate Fix (Auto-Recreate on Mismatch)
```python
if schema_mismatch_detected:
    print("Auto-fixing schema...")
    client.delete_collection()
    client.create_collection(with_named_vectors)
    print("✓ Fixed. Re-run --batch-ingest")
    sys.exit(0)
```

### Search Fallback Chain
```
1. Try named vector search ("image")
   ↓ (fails)
2. Try unnamed vector search
   ↓ (works but may return wrong vectors)
3. Python fallback (scroll + cosine)
   ↓ (always works)
4. Return results
```

## Key Code Locations

```
Issue → File → Line
─────────────────────────────────────────────────
Schema Init    → utils/qdrant_init.py → Line 20-50
Schema Check   → utils/qdrant_init.py → Line 35-45 (BROKEN)
Upsert Logic   → layers/ingestion/qdrant_upsert.py → __init__
Search Logic   → layers/search/hybrid_search.py → execute_search
Fallback       → layers/search/hybrid_search.py → _python_fallback_search
```

## Required Patches

1. ✓ Schema auto-detection in init
2. ✓ Auto-recreate on mismatch
3. ✓ Search fallback to unnamed vectors
4. ✓ Self-exclusion filter
5. ✓ Confidence moderation

## Execution Sequence (Fixed)

```bash
# Step 1: System detects schema mismatch and auto-fixes
python main.py
# → Drops old collection
# → Creates new with named vectors
# → Exits with message: "Run --batch-ingest"

# Step 2: Populate with correct schema
python main.py --batch-ingest
# → Ingests all 933 incidents with named vectors

# Step 3: Run demo
python main.py
# → Retrieves N similar incidents (excluding self)
# → Status: ACCEPT
# → Confidence: moderated by evidence count
```
