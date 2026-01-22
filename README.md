# 🛡️ Project Rakshak

> **15-Agent Multi-Modal Disaster Response System**  
> Qdrant-MAS Hackathon (Convolve 4.0) Submission  
> **Made by Shaunak Majumdar & Arnav Chauhan, IIT Kharagpur**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-green.svg)](https://qdrant.tech/)
[![Gemini 2.5](https://img.shields.io/badge/Gemini-2.5%20Flash-red.svg)](https://ai.google.dev/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-ff4b4b.svg)](https://streamlit.io/)

---

## 📋 Table of Contents

1. [Problem Statement](#-problem-statement)
2. [Our Solution](#-our-solution)
3. [Key Features](#-key-features)
4. [Quick Start (5 minutes)](#-quick-start-5-minutes)
5. [Detailed Installation](#-detailed-installation)
6. [Configuration](#️-configuration)
7. [Running the System](#-running-the-system)
8. [Using the Dashboard](#-using-the-dashboard)
9. [Project Structure](#-project-structure)
10. [Qdrant Features Used](#-qdrant-features-used)
11. [Architecture](#-architecture)
12. [Troubleshooting](#-troubleshooting)

---

## 🎯 Problem Statement

**Qdrant-MAS Challenge**: Build a Multi-Agent System using Qdrant for disaster response that can:
- Process multi-modal data (satellite imagery, voice, text)
- Use vector similarity search for historical disaster matching
- Provide real-time emergency response recommendations
- Scale efficiently with binary quantization

---

## 💡 Our Solution

**Project Rakshak** is an AI-powered disaster response system with **two operational modes**:

| Mode | Purpose | Key Tech |
|------|---------|----------|
| 🆘 **Distress Signal** | Real-time chat with victims, voice panic detection | Whisper STT, CLAP Audio |
| 🛰️ **Rakshak Intel** | Satellite imagery analysis, historical matching | DINOv2, Hybrid Search |

Both modes are powered by **15 specialized AI agents** orchestrated through a unified pipeline.

---

## ✨ Key Features

| Feature | Implementation |
|---------|----------------|
| 🛰️ **Satellite Image Analysis** | DINOv2 (ViT-B/14) → 768-dim dense vectors |
| 🔍 **Hybrid Search** | Dense + Sparse (BM25) with RRF Fusion |
| ⚡ **40x Faster Search** | Qdrant Binary Quantization |
| 🌐 **Geo-Radius Filtering** | Find nearby historical disasters |
| 🎙️ **Voice Input** | Whisper STT + CLAP panic detection |
| 🤖 **LLM Reports** | Gemini 2.5 Flash emergency reports |
| 📊 **Auto Visualizations** | 5 charts per analysis |
| 🖥️ **Interactive Dashboard** | Streamlit dark theme UI |

---

## ⚡ Quick Start (5 minutes)

### Prerequisites
- Python 3.10 or higher
- Qdrant running (local or cloud)
- Gemini API key

### One-Command Setup

```bash
# Clone the repo
git clone https://github.com/arnav-chauhan-kgpian/project-rakshak.git
cd project-rakshak

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

## ⚙️ Configuration

### Create `.env` from `.env.example`

This project uses environment variables for all API keys and database configuration.

1. Locate the file named **`.env.example`** in the project root.
2. Create a new file called **`.env`** in the same directory.
3. Copy the contents of `.env.example` into `.env`.
4. Replace the placeholder values with your own credentials.

Your `.env` file should look like this:

```env
# Qdrant Configuration
QDRANT_HOST="localhost"
QDRANT_PORT="6333"
QDRANT_URL="<YOUR QDRANT CLOUD ENDPOINT>"
QDRANT_API_KEY="<YOUR QDRANT API KEY>"

# Gemini API
GEMINI_API_KEY="<YOUR GEMINI API KEY>"


# Run!
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## 📦 Detailed Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/arnav-chauhan-kgpian/project-rakshak.git
cd project-rakshak
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

> ⏱️ First install may take 5-10 minutes (downloading PyTorch, Transformers, etc.)

### Step 4: Start Qdrant

**Option A: Docker**
```bash
docker pull qdrant/qdrant
docker run -p 6333:6333 -v .:/qdrant/storage qdrant/qdrant
```

**Option B: Qdrant Cloud**
1. Go to [cloud.qdrant.io](https://cloud.qdrant.io)
2. Create a free cluster
3. Copy your cluster URL and API key

**Option C: Download Binary**
```bash
# Download from https://github.com/qdrant/qdrant/releases
./qdrant
```

---

## ⚙️ Configuration

### Create `.env` file

Create a file named `.env` in the project root:

```env
# REQUIRED: Get from https://aistudio.google.com/
GEMINI_API_KEY=your_gemini_api_key_here

# Qdrant Connection
# Option 1: Local Qdrant
QDRANT_URL=http://localhost:6333

# Option 2: Qdrant Cloud (uncomment if using)
# QDRANT_URL=https://your-cluster.cloud.qdrant.io
# QDRANT_API_KEY=your_qdrant_api_key
```

### Get Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Click "Get API Key"
3. Create a new key
4. Copy and paste into `.env`

---

## 📂 Data Setup & Ingestion

To enable the historical matching capabilities (Rakshak Intel), you need to ingest the **xBD Disaster Dataset**.

### 1. Download the Dataset
We use the **xBD Dataset** (created by xView2 Challenge) for historical disaster data.
1. Download the dataset (specifically the **train** set is sufficient for demo). Dataset link - https://xview2.org/
2. Extract the files so your project structure looks like this:
   ```
   project-rakshak/
   ├── train/
   │   ├── images/       # Contains *_post_disaster.png files
   │   ├── labels/       # Contains JSON metadata
   |   └── targets/
   ```

### 2. Download Audio Dataset
We use a **911 Audio Dataset** (or similar emergency call dataset) for the distress signal pipeline.
1. Download standard emergency call samples (wav/mp3) and the metadata.csv. Dataset link - https://www.kaggle.com/datasets/louisteitelbaum/911-recordings/
2. Place them in:
   ```
   project-rakshak/
   ├── train_audio/   # Place audio files here
   │   ├── 911_recordings/
       ├── call_1.mp3
       ├── call_2.mp3
       .....
       └── 911_metadata.csv       
   ```

### 3. Ingest Embeddings
Run the batch ingestion script to generate DINOv2 (visual) and CLAP (audio) embeddings:

```bash
python main.py --reset --batch-ingest
```

> ⚠️ **Note:** This process generates:
> - **768-dim DINOv2 vectors** for satellite images
> - **512-dim CLAP vectors** for audio panic analysis
> It may take 10-20 minutes depending on your hardware.

---

## ▶️ Running the System

### Method 1: Streamlit Dashboard (Recommended)

```bash
streamlit run app.py
```

Then open **http://localhost:8501** in your browser.

### Method 2: Command Line Interface

```bash
python run_system.py
```

**CLI Menu:**
```
[1] 🚨 DISTRESS SIGNAL MODE (Victim Chat)
[2] 🌍 GUARDIAN OVERWATCH (Damage Assessment)
[3] 🖥️ LAUNCH DASHBOARD (Streamlit UI)
[t] 🔌 TERMINATE & SHOW UNIFIED TRIAGE
```

### Method 3: Direct Pipeline Execution

```bash
python main.py
```

---

## 🖥️ Using the Dashboard

### Home Screen

When you launch the app, you'll see three operation modes:

1. **🚀 LAUNCH CHAT** - Enter Distress Signal mode
2. **🚀 LAUNCH INTEL** - Enter Guardian Intel mode
3. **🚀 VIEW STATS** - See system analytics

### 🆘 Distress Signal Mode

1. Enter your GPS coordinates (or use defaults)
2. Type your emergency message OR use voice input
3. Chat with Guardian AI - it will:
   - Provide immediate safety advice
   - Dispatch emergency teams
   - Track your situation
4. Click "End Session & Generate Triage" for a full report

**Voice Input:**
- Click the 🎤 microphone button
- Speak your message
- Audio is transcribed via Whisper
- Panic level is detected via CLAP

### 🛰️ Guardian Intel Mode

1. **Input Tab:**
   - Set Latitude/Longitude
   - Select Disaster Type
   - Upload satellite image OR use file path
   - View location on map

2. **Click "Run Full 14-Agent Analysis"**

3. **Analysis Tab:**
   - Watch agents process in real-time
   - See progress bar

4. **Report Tab:**
   - View Emergency Report
   - See visualization charts
   - Check confidence score
   - Review triage priority

---

## 📁 Project Structure

```
guardian-overwatch/
├── app.py                    # 🖥️ Streamlit Dashboard
├── main.py                   # 👑 CentralCoordinator (15 Agents)
├── run_system.py             # 📟 CLI Menu System
├── chatbot_client.py         # 💬 CLI Chatbot
├── requirements.txt          # 📦 Dependencies
├── .env                      # 🔑 API Keys (create this)
│
├── layers/                   # 🤖 Agent Implementations
│   ├── ingestion/            # Layer 1: Perception
│   │   ├── satellite.py      # Image validation
│   │   ├── embedding.py      # DINOv2 embeddings
│   │   ├── sparse_embedding.py
│   │   ├── metadata.py
│   │   └── qdrant_upsert.py
│   │
│   ├── search/               # Layer 2: Retrieval
│   │   ├── search_processor.py
│   │   └── hybrid_search.py
│   │
│   └── reasoning/            # Layer 3: Reasoning
│       ├── geo_search.py     # GeoRadius search
│       ├── recomm.py         # Evidence synthesis
│       ├── history_summarizer.py
│       ├── llm_reasoning.py  # Gemini reports
│       ├── evaluator.py      # Report auditor
│       ├── post_processor.py
│       ├── explanation.py    # Chart generation
│       └── victim_chat.py    # Emergency chatbot
│
├── utils/                    # 🔧 Utilities
│   ├── voice_input.py        # Whisper + CLAP
│   └── async_utils.py        # Retry logic
│
├── imagery/                  # 🛰️ Sample images
├── reports/                  # 📄 Generated reports
├── chat_logs/                # 💬 Chat sessions
│
├── ARCHITECTURE.md           # 📐 System documentation
└── README.md                 # 📖 This file
```

---

## 🔧 Qdrant Features Used

| Feature | Where | Purpose |
|---------|-------|---------|
| **Dense Vectors** | `embedding.py` | DINOv2 768-dim visual embeddings |
| **Sparse Vectors** | `sparse_embedding.py` | BM25 keyword vectors |
| **Hybrid Search** | `hybrid_search.py` | RRF fusion (dense + sparse) |
| **Binary Quantization** | Collection config | 40x faster search, 2x oversampling |
| **GeoRadius Filter** | `geo_search.py` | Find disasters within km radius |
| **Payload Filtering** | `search_processor.py` | Filter by disaster_type |
| **Named Vectors** | `hybrid_search.py` | Separate "dense" + "sparse" |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GUARDIAN OVERWATCH                        │
├─────────────────────────────────────────────────────────────┤
│  LAYER 1: PERCEPTION          │  Satellite → DINOv2 → Qdrant │
│  LAYER 2: RETRIEVAL           │  Hybrid Search + GeoRadius   │
│  LAYER 3: REASONING           │  Gemini LLM → Report + Charts│
└─────────────────────────────────────────────────────────────┘
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the complete 15-agent Mermaid diagram.

---

## 🔍 Troubleshooting

### "GEMINI_API_KEY not found"
```bash
# Make sure .env file exists and contains:
GEMINI_API_KEY=your_key_here
```

### "Cannot connect to Qdrant"
```bash
# Check if Qdrant is running:
curl http://localhost:6333/health

# If not, start it:
docker run -p 6333:6333 -v .:/qdrant/storage qdrant/qdrant
```

### "ModuleNotFoundError"
```bash
# Reinstall dependencies:
pip install -r requirements.txt
```

### "CUDA out of memory"
```bash
# DINOv2 defaults to CPU if CUDA fails
# Or explicitly set:
export CUDA_VISIBLE_DEVICES=""
```

### Voice input not working
```bash
# Install audio dependencies:
pip install sounddevice soundfile
```

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Qdrant** - High-performance vector database
- **Google Gemini** - LLM reasoning capabilities
- **DINOv2** - Self-supervised visual embeddings
- **Whisper** - Speech-to-text transcription
- **CLAP** - Audio understanding
- **xBD Dataset** - Disaster imagery
- **Convolve 4.0** - Hackathon organizing team

---

<div align="center">

**Made with ❤️ by Shaunak Majumdar & Arnav Chauhan**  
**IIT Kharagpur**

</div>
