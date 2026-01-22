"""
Voice Input Utility for the Distress Chatbot.
Uses Deepgram API for Speech-to-Text.
Requires: deepgram-sdk, sounddevice, soundfile (pip install deepgram-sdk sounddevice soundfile)
"""

import os
import tempfile
from pathlib import Path

# Recording (Optional - requires sounddevice)
try:
    import sounddevice as sd
    import soundfile as sf
    RECORDING_AVAILABLE = True
except ImportError:
    RECORDING_AVAILABLE = False
    print("⚠️ Voice recording disabled. Install: pip install sounddevice soundfile")


# Local Audio Agent (Offline)
try:
    from layers.ingestion.audio import AudioIngestionAgent
    AUDIO_AGENT_AVAILABLE = True
except ImportError:
    AUDIO_AGENT_AVAILABLE = False
    print("⚠️ AudioIngestionAgent not found. Ensure layers/ingestion/audio.py exists.")

# Export for backward compatibility
WHISPER_AVAILABLE = AUDIO_AGENT_AVAILABLE


def record_audio(duration: float = 5.0, sample_rate: int = 16000) -> str:
    """
    Records audio from the microphone for `duration` seconds.
    Saves to a temp WAV file and returns the path.
    """
    if not RECORDING_AVAILABLE:
        print("❌ Recording not available. Please type your message instead.")
        return None
    
    print(f"🎙️ Recording for {duration} seconds... (Speak now!)")
    try:
        audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()  # Wait until recording is finished
        print("✅ Recording complete.")
        
        # Save to temp file
        temp_path = Path(tempfile.gettempdir()) / "distress_voice.wav"
        sf.write(str(temp_path), audio_data, sample_rate)
        return str(temp_path)
    except Exception as e:
        print(f"❌ Recording failed: {e}")
        return None


def transcribe_audio_local(audio_path: str, include_panic: bool = False):
    """
    Transcribes audio using local AudioIngestionAgent (Whisper).
    Optionally returns panic score from CLAP.
    """
    if not AUDIO_AGENT_AVAILABLE:
        print("❌ Local Audio Agent not available.")
        return None

    try:
        # Initialize agent (lazy load)
        if not hasattr(transcribe_audio_local, '_agent'):
            print("🔄 Initializing Local Whisper Model (One-time setup)...")
            transcribe_audio_local._agent = AudioIngestionAgent()
        
        agent = transcribe_audio_local._agent
        
        # Process audio
        print("🔄 Processing audio locally (Whisper + CLAP)...")
        result = agent.process_audio(audio_path)
        
        if not result or not result.get("transcription"):
            print("❌ No speech detected.")
            return None if not include_panic else (None, None)
            
        transcript = result.get("transcription", "").strip()
        print(f"📝 Transcribed: \"{transcript}\"")
        
        if include_panic:
            panic_level = agent.get_panic_proxy(result.get("embedding"))
            # Display panic indicator
            panic_icons = {"low": "🟢", "medium": "🟡", "high": "🟠", "extreme": "🔴"}
            print(f"  {panic_icons.get(panic_level, '⚪')} PANIC LEVEL: {panic_level.upper()}")
            return transcript, panic_level
            
        return transcript

    except Exception as e:
        print(f"❌ Local Audio processing error: {e}")
        return None if not include_panic else (None, None)


def get_voice_input(duration: float = 5.0, analyze_panic: bool = False):
    """
    Main function: Records audio and transcribes it using Local Model.
    
    Args:
        duration: Recording duration in seconds
        analyze_panic: If True, returns (transcript, panic_level, audio_path)
        
    Returns:
        str (transcript) if analyze_panic=False
        tuple (transcript, panic_level, audio_path) if analyze_panic=True
    """
    audio_path = record_audio(duration=duration)
    if not audio_path:
        return (None, None, None) if analyze_panic else None
    
    if analyze_panic:
        result = transcribe_audio_local(audio_path, include_panic=True)
        if result:
            transcript, panic_level = result
            return transcript, panic_level, audio_path
        return (None, None, audio_path)
    
    return transcribe_audio_local(audio_path, include_panic=False)



if __name__ == "__main__":
    # Test the voice input
    print("=== Voice Input Test (Local Whisper) ===")
    text = get_voice_input(duration=5.0)
    if text:
        print(f"You said: {text}")
    else:
        print("Voice input failed.")
