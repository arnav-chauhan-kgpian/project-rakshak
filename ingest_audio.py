"""
Audio Ingestion Script
Batch ingests .mp3/.wav files into Qdrant 'disaster_audio' collection (512-dim CLAP).
"""
import os
import sys
import glob
from pathlib import Path
from tqdm import tqdm
from utils.qdrant_init import initialize_qdrant
from layers.ingestion.audio import AudioIngestionAgent
from qdrant_client.models import PointStruct

def ingest_audio_folder(audio_dir="audio_data", limit=None):
    """
    Ingests audio files from the directory.
    Args:
        audio_dir: Directory containing audio files
        limit: Max number of files to process (None for all)
    """
    print(f"\n🎧 AUDIO INGESTION STARTED")
    print(f"   Target Directory: {audio_dir}")
    if limit:
        print(f"   Limit: {limit} files")
    
    # 1. Initialize Qdrant
    client = initialize_qdrant()
    collection_name = "disaster_audio"
    
    # 2. Initialize Audio Agent
    agent = AudioIngestionAgent()
    
    # 3. Find files
    extensions = ["*.wav", "*.mp3", "*.m4a"]
    files = []
    for ext in extensions:
        files.extend(list(Path(audio_dir).rglob(ext)))
    
    if not files:
        print(f"❌ No audio files found in {audio_dir}")
        return
        
    # Apply limit
    if limit and len(files) > limit:
        files = files[:limit]
        
    print(f"   Found {len(files)} audio files to process.")
    
    # 4. Process Loop
    success_count = 0
    error_count = 0
    
    for i, file_path in enumerate(tqdm(files, desc="Processing Audio")):
        try:
            # Process (Whisper + CLAP)
            result = agent.process_audio(str(file_path))
            
            if not result:
                error_count += 1
                continue
                
            # Create Point
            incident_id = file_path.stem
            
            # Metadata payload
            payload = {
                "filename": file_path.name,
                "incident_id": incident_id,
                "transcription": result["transcription"],
                "duration": result["duration"],
                "type": "911_call"
            }
            
            # Upsert
            client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=i,  # Simple integer ID for audio
                        vector={
                            "audio": result["embedding"]
                        },
                        payload=payload
                    )
                ]
            )
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Error processing {file_path.name}: {e}")
            error_count += 1
            
    print(f"\n✅ Ingestion Complete!")
    print(f"   Success: {success_count}")
    print(f"   Failed:  {error_count}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest audio files into Qdrant for panic detection.")
    parser.add_argument("dir", nargs="?", default="audio_data", help="Directory containing audio files")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of files to ingest")
    
    args = parser.parse_args()
    
    # Create dir if not exists
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
        print(f"Created directory: {args.dir} - Please put audio files here!")
    else:
        ingest_audio_folder(args.dir, args.limit)
