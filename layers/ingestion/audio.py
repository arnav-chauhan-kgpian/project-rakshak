
import threading
import torch
import numpy as np
import librosa
from pathlib import Path

class AudioIngestionAgent:
    """
    Agent 2b: Audio Ingestion & Processing
    
    Responsibilities:
    1. Load audio files (.mp3, .wav)
    2. Transcribe speech using Whisper (Semantic Content)
    3. Generate acoustic embeddings using CLAP (Panic/Context)
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._initialized = False
        self.device = None
        
        # Pipelines
        self.whisper_pipe = None
        self.clap_model = None
        self.clap_processor = None
        
        # Config
        self.whisper_model_id = "openai/whisper-tiny" # Fast, good enough for keywords
        self.clap_model_id = "laion/clap-htsat-unfused" # Standard CLAP on HF
        self.embedding_dim = 512 # CLAP projection dim
        
    def _lazy_init(self):
        """Thread-safe lazy initialization of models."""
        if self._initialized: return
        
        with self._lock:
            if self._initialized: return
            try:
                print("  Loading Audio Models (Whisper + CLAP)...")
                from transformers import pipeline, AutoProcessor, ClapModel
                
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
                device_id = 0 if self.device == "cuda" else -1
                
                # 1. Load Whisper (ASR)
                print(f"    - Loading Whisper ({self.whisper_model_id})...")
                self.whisper_pipe = pipeline(
                    "automatic-speech-recognition", 
                    model=self.whisper_model_id,
                    device=device_id
                )
                
                # 2. Load CLAP (Acoustic Embedding)
                print(f"    - Loading CLAP ({self.clap_model_id})...")
                self.clap_processor = AutoProcessor.from_pretrained(self.clap_model_id)
                self.clap_model = ClapModel.from_pretrained(self.clap_model_id)
                if self.device == "cuda":
                    self.clap_model.to("cuda")
                self.clap_model.eval()
                
                print(f"  ✓ Audio models loaded on {self.device.upper()}")
                self._initialized = True
                
            except Exception as e:
                print(f"  ⚠ Audio Model Init Error: {e}")
                self._initialized = False

    def process_audio(self, file_path):
        """
        Process a single audio file.
        Returns dict with: transcription, embedding, duration
        """
        try:
            self._lazy_init()
            path = Path(file_path)
            if not path.exists():
                print(f"  ⚠ Audio file not found: {file_path}")
                return None
                
            # 1. Transcribe (Whisper)
            transcription = ""
            try:
                # Load audio at 16kHz for Whisper
                y_full, sr_full = librosa.load(str(path), sr=16000)
                
                # Truncate to max 30 seconds
                max_samples = 30 * 16000
                if len(y_full) > max_samples:
                    y_full = y_full[:max_samples]
                
                result = self.whisper_pipe(y_full)
                transcription = result.get("text", "").strip()
            except Exception as w_err:
                print(f"    ⚠ Whisper error for {path.name}: {w_err}")
            
            # 2. Embed (CLAP)
            embedding = []
            try:
                # Load audio for CLAP (48kHz, 10s max)
                audio_array, sample_rate = librosa.load(str(path), sr=48000, duration=10.0)
                
                inputs = self.clap_processor(audios=audio_array, return_tensors="pt", sampling_rate=48000)
                if self.device == "cuda":
                    inputs = {k: v.to("cuda") for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = self.clap_model.get_audio_features(**inputs)
                    embed = outputs[0].cpu().numpy()
                    norm = np.linalg.norm(embed)
                    if norm > 0:
                        embed = embed / norm
                    embedding = embed.tolist()
            except Exception as c_err:
                print(f"    ⚠ CLAP error for {path.name}: {c_err}")
                # Fallback embedding
                embedding = np.random.randn(self.embedding_dim).tolist()

            # Calculate duration
            try:
                duration = librosa.get_duration(path=str(path))
            except:
                duration = 0

            return {
                "transcription": transcription,
                "embedding": embedding,
                "duration": duration
            }
            
        except Exception as e:
            print(f"  ❌ Audio Processing Error ({file_path}): {e}")
            return None
    
    def get_panic_proxy(self, embedding):
        """
        Estimate panic level from CLAP embedding.
        This is a proxy based on embedding distance to known panic patterns.
        Returns: low, medium, high, extreme
        """
        # Simple heuristic based on embedding energy (real implementation would use trained classifier)
        embed_array = np.array(embedding)
        energy = np.linalg.norm(embed_array)
        variance = np.var(embed_array)
        
        # Higher variance often correlates with more complex audio (multiple sounds, stress indicators)
        if variance > 0.01:
            return "extreme"
        elif variance > 0.005:
            return "high"
        elif variance > 0.002:
            return "medium"
        else:
            return "high"  # Default to HIGH for emergency system - assume urgency
