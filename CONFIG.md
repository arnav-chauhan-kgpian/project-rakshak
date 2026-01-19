# Configuration Guide

## Environment Setup

### 1. Python Environment

```bash
# Using venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Using conda
conda create -n disaster python=3.9
conda activate disaster
```

### 2. Qdrant Server

```bash
# Using Docker (recommended)
docker run -p 6333:6333 qdrant/qdrant

# Verify Qdrant is running
curl http://localhost:6333/health
# Expected: {"title":"Qdrant",...,"status":"ok"}

# Using local installation
# Download from: https://qdrant.tech
# Run: ./qdrant
```

### 3. Dependencies

```bash
pip install -r requirements.txt

# Verify installations
python -c "import qdrant_client; print('✓ Qdrant client')"
python -c "import torch; print('✓ PyTorch')"
python -c "import numpy; print('✓ NumPy')"
```

## Agent Configuration

### Query Planner Configuration

Edit `layers/search/query_planner.py` to customize search strategies:

```python
self.filter_strategies = {
    "earthquake": {
        "spatial_radius_km": 50,      # Search radius
        "temporal_days": 30,           # Historical window
        "severity_threshold": 0.6      # Confidence threshold
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
}
```

### Validator Configuration

Edit `layers/search/validator.py`:

```python
self.score_threshold = 0.60      # Minimum acceptance score
self.required_results = 3        # Minimum similar incidents
```

### Confidence Calibration

Edit `layers/reasoning/confidence.py`:

```python
weights = {
    "vector_similarity": 0.6,        # Weight for vector score
    "evidence_quality": 0.4          # Weight for evidence quality
}
self.base_calibration = 0.7         # Base calibration factor
```

### Priority Thresholds

Edit `layers/reasoning/priority.py`:

```python
self.priority_thresholds = {
    "low": (0.0, 0.5),
    "medium": (0.5, 0.7),
    "high": (0.7, 0.85),
    "critical": (0.85, 1.0)
}
```

## Qdrant Configuration

### Collection Setup

The `utils/qdrant_init.py` creates the following:

```python
collection_name="disaster_memory"
vectors_config=VectorParams(
    size=768,                    # DINOv2 embedding dimension
    distance=Distance.COSINE     # Similarity metric
)
```

### Payload Schema

Standard Qdrant payload fields (auto-managed):

```python
{
    "incident_id": str,
    "disaster_type": str,
    "timestamp": str,
    "latitude": float,
    "longitude": float,
    "damage_severity": str,
    "confidence_score": float,
    "full_metadata": dict
}
```

### Customizing Collection

To change collection parameters:

```python
# In utils/qdrant_init.py
client.recreate_collection(
    collection_name="disaster_memory",
    vectors_config=VectorParams(
        size=1024,                    # Change dimension if using different model
        distance=Distance.COSINE      # or Distance.EUCLIDEAN
    ),
)
```

## Embedding Configuration

### DINOv2 Model Selection

Edit `layers/ingestion/embedding.py`:

```python
model_name = "dinov2_vitb14"  # Options:
# dinov2_vits14       - Small (384-dim) - Faster
# dinov2_vitb14       - Base (768-dim) - Default
# dinov2_vitl14       - Large (1024-dim) - More accurate
# dinov2_vitg14       - Giant (1536-dim) - Most accurate
```

### Image Preprocessing

In `embedding.py`, customize preprocessing:

```python
img_resized = img.resize((224, 224))  # DINOv2 standard size

# Can also normalize differently:
img_array = (np.array(img_resized) / 255.0) * 2 - 1  # [-1, 1] normalization
```

## LLM Integration

### OpenAI Configuration (for production)

Add to `layers/reasoning/llm_reasoning.py`:

```python
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

# In generate_report method:
response = openai.ChatCompletion.create(
    model="gpt-4-vision",
    messages=[{
        "role": "user",
        "content": f"Generate damage assessment: {prompt}"
    }],
    temperature=0.7,
    max_tokens=1000
)
```

### Alternative LLM Providers

```python
# Claude (Anthropic)
from anthropic import Anthropic
client = Anthropic()

# Local LLM (Ollama)
import ollama
response = ollama.generate(model="llama2", prompt=text)
```

## Performance Tuning

### Vector Search Optimization

```python
# In layers/search/hybrid_search.py
# Increase search limit for accuracy/latency tradeoff
search_results = self.client.search(
    collection_name="disaster_memory",
    query_vector=query_vector,
    query_filter=filter_obj,
    limit=20,  # Increase from 10 for more results
    score_threshold=0.5  # Add score filter
)
```

### Batch Processing

For multiple incidents:

```python
from main import CentralCoordinator

coordinator = CentralCoordinator()
incidents = [
    ("image1.png", 34.05, -118.24, "earthquake"),
    ("image2.png", 34.10, -118.20, "earthquake"),
    ("image3.png", 40.71, -74.01, "flood")
]

results = []
for img, lat, lon, dtype in incidents:
    result = coordinator.process_new_incident(img, lat, lon, dtype)
    results.append(result)
```

### Memory Management

For large-scale deployments:

```python
# Clear embeddings cache periodically
import gc
gc.collect()

# Use batch API for embeddings
from torch.utils.data import DataLoader
# Load images in batches for parallel embedding extraction
```

## Logging Configuration

Add logging to `main.py`:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('disaster_mas.log'),
        logging.StreamHandler()
    ]
)
```

## API Keys & Secrets

Create a `.env` file:

```
QDRANT_URL=http://localhost:6333
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
MAPBOX_TOKEN=pk_...
```

Load in `main.py`:

```python
from dotenv import load_dotenv
import os

load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")
```

## Debugging

### Enable Verbose Logging

```python
# In main.py
coordinator = CentralCoordinator()

# Add debugging
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
```

### Check Qdrant Status

```bash
# Health check
curl http://localhost:6333/health

# Collection info
curl http://localhost:6333/collections/disaster_memory

# Search metrics
curl http://localhost:6333/telemetry
```

### Test Individual Agents

```python
# Test embedding agent
from layers.ingestion.embedding import EmbeddingAgent
agent = EmbeddingAgent()
embedding = agent.get_embedding("test.png")
print(f"Embedding shape: {len(embedding)}")

# Test query planner
from layers.search.query_planner import QueryPlannerAgent
planner = QueryPlannerAgent()
plan = planner.plan_query(34.05, -118.24, "earthquake")
print(f"Plan: {plan}")
```

## Production Deployment

### Docker Setup

Create `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Build and run:

```bash
docker build -t disaster-mas .
docker run -p 5000:5000 --link qdrant:qdrant disaster-mas
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  disaster-mas:
    build: .
    ports:
      - "5000:5000"
    depends_on:
      - qdrant
    environment:
      QDRANT_URL: http://qdrant:6333

volumes:
  qdrant_data:
```

Run: `docker-compose up`

## Monitoring

### System Health

```python
import psutil

def check_system_health():
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }
```

### Agent Metrics

Add to each agent:

```python
import time

class Agent:
    def __init__(self):
        self.execution_times = []
        self.error_count = 0
    
    def process(self):
        start = time.time()
        try:
            # Process logic
            pass
        except:
            self.error_count += 1
        self.execution_times.append(time.time() - start)
```

---

**Last Updated**: January 2026
**Version**: 1.0
