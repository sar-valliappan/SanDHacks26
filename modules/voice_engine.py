
import os
import re
import json
import time
from dotenv import load_dotenv

load_dotenv()

FILLER_PHRASES = [
    "um", "uh", "like", "you know", "basically", "actually", "literally", "sort of", "kind of", "i mean", "right"
]

def extract_metrics(transcript: str, segments: list = None, duration_seconds: float = 30.0) -> dict:
    """Extract speech metrics from transcript."""
    clean = transcript.strip()
    words = re.findall(r"\b[\w']+\b", clean)
    word_count = len(words)

    lower = clean.lower()
    filler_counts = {}
    total_fillers = 0
    for phrase in FILLER_PHRASES:
        pattern = rf"(?<!\w){re.escape(phrase)}(?!\w)"
        count = len(re.findall(pattern, lower))
        if count > 0:
            filler_counts[phrase] = count
            total_fillers += count

    duration_seconds = max(duration_seconds, 1.0)
    pace_wpm = int(round(word_count / (duration_seconds / 60.0))) if word_count > 0 else 0
    
    # Estimate pauses from segments
    pause_count = 0
    if segments and len(segments) > 1:
        for i in range(1, len(segments)):
            prev_end = segments[i-1].get('end', 0)
            curr_start = segments[i].get('start', 0)
            gap = curr_start - prev_end
            if gap > 0.5:
                pause_count += 1
    
    sentence_count = len([s for s in re.split(r"[.!?]+", clean) if s.strip()])

    return {
        "word_count": word_count,
        "sentence_count": sentence_count,
        "pace_wpm": pace_wpm,
        "filler_words": filler_counts if filler_counts else {},
        "total_fillers": total_fillers,
        "pause_count": pause_count,
        "duration_seconds": round(duration_seconds, 1)
    }


def wait_for_file_active(genai_file, timeout=60):
    """Wait for uploaded file to become ACTIVE state."""
    import google.generativeai as genai
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        file_status = genai.get_file(genai_file.name)
        if file_status.state.name == "ACTIVE":
            return True
        elif file_status.state.name == "FAILED":
            return False
        print(f"[INFO] Waiting for file to be ready... ({file_status.state.name})")
        time.sleep(2)
    return False


def get_video_duration(file_path: str) -> float:
    """Get actual video duration using ffprobe or file size estimate."""
    try:
        import subprocess
        result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration', '-of', 'csv=p=0', file_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except:
        pass
    
    # Fallback: estimate from file size (~50KB per second for webm)
    try:
        size = os.path.getsize(file_path)
        return max(5.0, size / 50000)
    except:
        return 30.0


def transcribe_with_gemini(file_path: str) -> dict:
    """Use Gemini to transcribe audio/video and detect pauses."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"text": "", "segments": [], "pause_count": 0, "error": "No API key"}
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        print(f"[INFO] Uploading file for transcription: {file_path}")
        uploaded_file = genai.upload_file(file_path)
        
        # Wait for file to become active
        if not wait_for_file_active(uploaded_file):
            return {"text": "", "segments": [], "pause_count": 0, "error": "File upload failed"}
        
        print("[INFO] File ready, transcribing with pause detection...")
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        response = model.generate_content([
            """Listen to this recording carefully and provide:
            
1. TRANSCRIPT: Transcribe EXACTLY what the person says, word for word. Include all filler words like "um", "uh", "like", etc.

2. PAUSE_COUNT: Count the number of significant pauses (silence or hesitation of 2+ seconds) during the response. This includes:
   - Long gaps before starting to speak
   - Pauses mid-sentence where the speaker hesitates
   - Moments of silence between thoughts

Return your response in this exact format:
TRANSCRIPT: [the transcript here]
PAUSE_COUNT: [number]""",
            uploaded_file
        ])
        
        # Cleanup
        try:
            uploaded_file.delete()
        except:
            pass
        
        # Parse response
        text = response.text.strip()
        transcript = ""
        pause_count = 0
        
        if "TRANSCRIPT:" in text:
            parts = text.split("PAUSE_COUNT:")
            transcript = parts[0].replace("TRANSCRIPT:", "").strip()
            if len(parts) > 1:
                try:
                    pause_count = int(parts[1].strip().split()[0])
                except:
                    pause_count = 0
        else:
            transcript = text
        
        print(f"[INFO] Transcript: {transcript[:100]}...")
        print(f"[INFO] Detected pauses: {pause_count}")
        return {"text": transcript, "segments": [], "pause_count": pause_count}
        
    except Exception as e:
        print(f"[ERROR] Transcription failed: {e}")
        import traceback
        traceback.print_exc()
        return {"text": "", "segments": [], "pause_count": 0, "error": str(e)}


def analyze_audio_with_gemini(file_path: str) -> dict:
    """Analyze vocal tone, confidence, etc."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {}
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        print(f"[INFO] Analyzing audio tone...")
        uploaded_file = genai.upload_file(file_path)
        
        if not wait_for_file_active(uploaded_file):
            return {"error": "File upload failed"}
        
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        response = model.generate_content([
            """Analyze the speaker's voice in this recording. Return a JSON object with:
            - confidence_level: "high", "medium", or "low"
            - tone: one of "professional", "casual", "nervous", "enthusiastic", "hesitant"
            - energy: "high", "moderate", or "low"  
            - clarity: "clear", "somewhat clear", or "unclear"
            - emotion: main detected emotion
            Return ONLY valid JSON.""",
            uploaded_file
        ])
        
        try:
            uploaded_file.delete()
        except:
            pass
        
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        
        return json.loads(text)
        
    except Exception as e:
        print(f"[ERROR] Audio analysis failed: {e}")
        return {"confidence_level": "medium", "tone": "professional"}


def process_file(file_path: str) -> dict:
    """Process audio/video file and return full analysis."""
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}
    
    print(f"[INFO] Processing: {file_path}")
    
    # Get actual duration
    duration = get_video_duration(file_path)
    print(f"[INFO] Video duration: {duration:.1f}s")
    
    # 1. Transcribe
    print("[INFO] Starting transcription...")
    stt_result = transcribe_with_gemini(file_path)
    transcript = stt_result.get("text", "")
    segments = stt_result.get("segments", [])
    
    if not transcript:
        print("[WARN] No transcript generated")
    
    # Get pause count from transcription
    pause_count = stt_result.get("pause_count", 0)
    
    # 2. Extract metrics
    print("[INFO] Extracting metrics...")
    metrics = extract_metrics(transcript, segments, duration_seconds=duration)
    # Override pause_count with Gemini's detection
    metrics["pause_count"] = pause_count
    
    # 3. Analyze audio tone
    print("[INFO] Analyzing tone...")
    analysis = analyze_audio_with_gemini(file_path)
    
    return {
        "transcript": transcript,
        "segments": segments,
        "metrics": metrics,
        "analysis": analysis
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = process_file(sys.argv[1])
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python voice_engine.py <audio_file>")
