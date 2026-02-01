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

def groq_transcribe(audio_bytes: bytes, file_ext: str = ".wav") -> dict:
    """
    Groq Whisper STT.
    Pass audio as (filename, bytes) so the SDK knows the format.
    Returns: {"text": str, "segments": list}
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GROQ_API_KEY in environment/.env")

    from groq import Groq
    client = Groq(api_key=api_key)

    filename = f"audio{file_ext}"  # e.g. audio.m4a, audio.wav
    
    # Use verbose_json to get segments/timestamps
    result = client.audio.transcriptions.create(
        file=(filename, audio_bytes),
        model="whisper-large-v3",
        response_format="verbose_json"
    )

    # result is a dictionary-like object when using verbose_json in Groq/OpenAI client
    # It has 'text' and 'segments'
    return {
        "text": result.text,
        "segments": result.segments
    }


def transcribe_and_analyze(audio_bytes: bytes, duration_seconds: float = 30.0, file_ext: str = ".wav") -> dict:
    """
    Returns:
      {
        "transcript": str,
        "segments": list, # New field with timestamps
        "metrics": { pace_wpm, filler_words, pause_count, ... }
      }
    """

    segments = []
    
    if STT_PROVIDER == "groq":
        result = groq_transcribe(audio_bytes, file_ext=file_ext)
        transcript = result.get("text", "")
        segments = result.get("segments", [])
    else:
        print("[INFO] Using MOCK STT provider (set STT_PROVIDER='groq' to use real API)")
        # Mock transcript fallback (demo-safe)
        transcript = (
            "I led a project under pressure when our deadline changed. "
            "Um, like, we had to reorganize fast."
        )
        # Mock segments
        segments = [
            {"start": 0.0, "end": 2.5, "text": "I led a project under pressure when our deadline changed."},
            {"start": 3.0, "end": 6.0, "text": "Um, like, we had to reorganize fast."}
        ]

    metrics = extract_metrics(transcript, duration_seconds=duration_seconds)
    return {"transcript": transcript, "segments": segments, "metrics": metrics}

    metrics = extract_metrics(transcript, duration_seconds=duration_seconds)
    return {"transcript": transcript, "segments": segments, "metrics": metrics}

def analyze_tone(file_path: str, mime_type: str = "audio/wav") -> dict:
    """
    Uses Gemini to analyze the vocal tone and emotion of the audio.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
         print("[INFO] Skipping tone analysis: GEMINI_API_KEY not found.")
         return {"tone": "unknown", "emotion": "unknown", "intensity": "unknown"}

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Upload the file to Gemini
        # Note: For efficiency in production, consider inline data if file is small, 
        # or File API if large. Here we use File API for simplicity.
        audio_file = genai.upload_file(file_path, mime_type=mime_type)
        
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        
        prompt = """
        Listen to this audio clip. Analyze the speaker's vocal tone and emotion.
        Return ONLY a JSON object with these keys:
        - emotion: (e.g., confident, nervous, excited, neutral)
        - tone: (e.g., professional, casual, hesitancy, formal)
        - intensity: (low, medium, high)
        - reasoning: brief explanation
        """
        
        result = model.generate_content([prompt, audio_file])
        
        # Cleanup
        try:
            audio_file.delete()
        except:
            pass
            
        # Parse JSON from response
        text = result.text.strip()
        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("\n", 1)[0]
        
        import json
        return json.loads(text)
        
    except Exception as e:
        print(f"[ERROR] Tone analysis failed: {e}")
        return {"error": str(e)}

def process_file(file_path: str) -> dict:
    """
    Reads an audio file and processes it using the transcription engine.
    """
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
        
    try:
        with open(file_path, "rb") as f:
            audio_bytes = f.read()
            
        # Determine file extension and mime type
        _, ext = os.path.splitext(file_path)
        mime_type = "audio/wav"
        if ext.lower() in [".m4a", ".mp4"]:
            mime_type = "audio/mp4"
        elif ext.lower() == ".mp3":
            mime_type = "audio/mp3"
        
        # Determine duration
        duration = 30.0
        if ext.lower() == ".wav":
            import wave
            try:
                with wave.open(file_path, 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration = frames / float(rate)
            except Exception:
                pass 
        
        # 1. Transcribe
        stt_result = transcribe_and_analyze(audio_bytes, duration_seconds=duration, file_ext=ext)
        
        # 2. Analyze Tone (Parallelizable in future)
        tone_result = analyze_tone(file_path, mime_type=mime_type)
        
        # Merge results
        stt_result["analysis"] = tone_result
        
        return stt_result
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
