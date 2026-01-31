import re

FILLER_PHRASES = [
    "um",
    "uh",
    "like",
    "you know",
    "basically",
    "actually",
    "literally",
    "sort of",
    "kind of",
]

def extract_metrics(transcript: str, duration_seconds: float = 30.0) -> dict:
    """
    Compute simple speech metrics from the transcript.
    duration_seconds can be passed in later from the actual audio length.
    """
    clean = transcript.strip()
    words = re.findall(r"\b[\w']+\b", clean)
    word_count = len(words)

    # Fillers: count occurrences of each phrase (case-insensitive)
    lower = clean.lower()
    filler_counts = {}
    for phrase in FILLER_PHRASES:
        # match whole phrase boundaries
        pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
        filler_counts[phrase] = len(re.findall(pattern, lower))

    # Pace estimate (words per minute)
    # Avoid divide-by-zero
    duration_seconds = max(duration_seconds, 1.0)
    pace_wpm = int(round(word_count / (duration_seconds / 60.0)))

    # A very rough pause estimate:
    # If you don't have timestamps yet, this is just a proxy.
    # Later you'll compute pauses from word-level timestamps.
    pause_count = filler_counts.get("um", 0) + filler_counts.get("uh", 0)

    # Optional: "sentences" can help with clarity feedback
    sentence_count = len([s for s in re.split(r"[.!?]+", clean) if s.strip()])

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "pace_wpm": pace_wpm,
        "filler_words": filler_counts,
        "pause_count": pause_count,
    }

def transcribe_and_analyze(audio_bytes: bytes, duration_seconds: float = 30.0) -> dict:
    """
    STEP 3 version:
    - Still uses a mocked transcript (no Wispr Flow yet)
    - Computes real metrics from transcript
    """
    # Mock transcript for now (replace later with Wispr Flow)
    transcript = "I led a project under pressure when our deadline changed. Um, like, we had to reorganize fast."

    metrics = extract_metrics(transcript, duration_seconds=duration_seconds)

    return {
        "transcript": transcript,
        "metrics": metrics,
    }

