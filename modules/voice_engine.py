def transcribe_and_analyze(audio_bytes):
    """
    Input: raw audio bytes (wav / webm converted upstream)
    Output:
      {
        "transcript": str,
        "metrics": {
          "pace_wpm": int,
          "filler_words": dict,
          "pause_count": int
        }
      }
    """
    return {
        "transcript": "I led a project under pressure when our deadline changed.",
        "metrics": {
            "pace_wpm": 145,
            "filler_words": {"um": 2, "like": 1},
            "pause_count": 4
        }
    }
