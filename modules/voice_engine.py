import os
import re

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
        # Mock transcript fallback (demo-safe)
        transcript = (
            "I led a project under pressure when our deadline changed. "
            "Um, like, we had to reorganize fast."
        )

    metrics = extract_metrics(transcript, duration_seconds=duration_seconds)
    return {"transcript": transcript, "metrics": metrics}
