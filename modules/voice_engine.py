import os
import re
from dotenv import load_dotenv

# Load environment variables explicitly
load_dotenv()

# Toggle between mock and groq without breaking teammates
STT_PROVIDER = os.getenv("STT_PROVIDER", "mock")  # "mock" or "groq"

FILLER_PHRASES = [
    "um", "uh", "like", "you know", "basically", "actually", "literally", "sort of", "kind of"
]

def extract_metrics(transcript: str, duration_seconds: float = 30.0) -> dict:
    clean = transcript.strip()
    words = re.findall(r"\b[\w']+\b", clean)
    word_count = len(words)

    lower = clean.lower()
    filler_counts = {}
    for phrase in FILLER_PHRASES:
        pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
        filler_counts[phrase] = len(re.findall(pattern, lower))

    duration_seconds = max(duration_seconds, 1.0)
    pace_wpm = int(round(word_count / (duration_seconds / 60.0)))

    # crude proxy until you have word timestamps
    pause_count = filler_counts.get("um", 0) + filler_counts.get("uh", 0)

    sentence_count = len([s for s in re.split(r"[.!?]+", clean) if s.strip()])

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "pace_wpm": pace_wpm,
        "filler_words": filler_counts,
        "pause_count": pause_count,
    }

def groq_transcribe(audio_bytes: bytes, file_ext: str = ".wav") -> str:
    """
    Groq Whisper STT.
    Pass audio as (filename, bytes) so the SDK knows the format.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY in environment/.env")

    from groq import Groq
    client = Groq(api_key=api_key)

    filename = f"audio{file_ext}"  # e.g. audio.m4a, audio.wav
    result = client.audio.transcriptions.create(
        file=(filename, audio_bytes),   # ✅ key fix
        model="whisper-large-v3"
    )

    return result.text


def transcribe_and_analyze(audio_bytes: bytes, duration_seconds: float = 30.0, file_ext: str = ".wav") -> dict:
    """
    Returns:
      {
        "transcript": str,
        "metrics": { pace_wpm, filler_words, pause_count, ... }
      }
    """

    if STT_PROVIDER == "groq":
        transcript = groq_transcribe(audio_bytes, file_ext=file_ext)
    else:
        print("[INFO] Using MOCK STT provider (set STT_PROVIDER='groq' to use real API)")
        # Mock transcript fallback (demo-safe)
        transcript = (
            "I led a project under pressure when our deadline changed. "
            "Um, like, we had to reorganize fast."
        )

    metrics = extract_metrics(transcript, duration_seconds=duration_seconds)
    return {"transcript": transcript, "metrics": metrics}

def process_file(file_path: str) -> dict:
    """
    Reads an audio file and processes it using the transcription engine.
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
        
    try:
        with open(file_path, "rb") as f:
            audio_bytes = f.read()
            
        # Determine file extension
        _, ext = os.path.splitext(file_path)
        
        # Determine duration - for now, we'll estimate or use default since reading duration from bytes is complex without extra libs
        # Ideally, we should use wave module or similar if we want exact duration, but for now 30.0 default is fine for metrics
        # If the file is a wav file, we can try to get duration
        duration = 30.0
        if ext.lower() == ".wav":
            import wave
            try:
                with wave.open(file_path, 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration = frames / float(rate)
            except Exception:
                pass # Fallback to default
        
        return transcribe_and_analyze(audio_bytes, duration_seconds=duration, file_ext=ext)
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import sys
    # Add parent directory to path to find config
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from config import Config
    
    # Check for command line argument, otherwise use default from get_recording.py
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
    else:
        # Default path where get_recording.py saves it
        if "data" not in os.listdir("."):
             # Try to find data dir relative to script if run from root
             audio_file = os.path.join("data", "test_audio.wav")
        else:
             audio_file = "data/test_audio.wav"
             
        # Check absolute path fallback from config if imported
        if not os.path.exists(audio_file):
             # Try Config.DATA_DIR
             audio_file = os.path.join(Config.DATA_DIR, "test_audio.wav")
    
    print(f"Processing audio file: {audio_file}")
    result = process_file(audio_file)
    print("Result:")
    print(result)
