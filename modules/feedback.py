import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from voice_engine import process_file

# Load API keys
load_dotenv()

def get_comprehensive_feedback(audio_file_path: str) -> dict:
    """
    Main entry point: Combines technical delivery metrics and AI content analysis.
    """
    # 1. Fetch raw data from voice_engine
    # This gives us the transcript, WPM, filler counts, and basic tone.
    raw_data = process_file(audio_file_path)
    
    if "error" in raw_data:
        return raw_data

    transcript = raw_data.get("transcript", "")
    metrics = raw_data.get("metrics", {})
    tone_analysis = raw_data.get("analysis", {})

    # 2. Delivery Analysis (Rule-based feedback)
    delivery_feedback = analyze_delivery(metrics, tone_analysis)

    # 3. Content Analysis (Gemini-based feedback)
    content_feedback = analyze_content_with_gemini(transcript)

    # 4. Final Merged Response
    return {
        "status": "success",
        "transcript": transcript,
        "delivery": delivery_feedback,
        "content": content_feedback,
        "raw_metrics": metrics
    }

def analyze_delivery(metrics: dict, tone: dict) -> dict:
    """
    Evaluates HOW the user spoke using the metrics from voice_engine.
    """
    pace = metrics.get("pace_wpm", 0)
    fillers = metrics.get("filler_words", {})
    total_fillers = sum(fillers.values())
    
    # Pacing logic
    if pace > 170:
        pace_msg = "Fast. You sound energetic, but try to pause so the interviewer can keep up."
    elif pace < 110:
        pace_msg = "Slow. Consider picking up the tempo to show more enthusiasm."
    else:
        pace_msg = "Ideal. Your speaking rate is professional and easy to follow."

    return {
        "pacing": {
            "wpm": pace,
            "feedback": pace_msg
        },
        "fillers": {
            "total_count": total_fillers,
            "breakdown": fillers,
            "feedback": "Try to replace fillers with silence." if total_fillers > 5 else "Great job minimizing filler words!"
        },
        "vibe": {
            "emotion": tone.get("emotion"),
            "tone": tone.get("tone"),
            "reasoning": tone.get("reasoning")
        }
    }

def analyze_content_with_gemini(transcript: str) -> dict:
    """
    Evaluates WHAT the user said using Gemini 2.0.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "Missing GEMINI_API_KEY"}

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""
    Analyze this interview answer transcript: "{transcript}"
    
    Provide feedback in JSON format:
    - score: (integer 1-100)
    - star_method: (Did they use Situation, Task, Action, Result? Answer "Yes", "Partial", or "No")
    - strengths: (list of 2 strings)
    - weaknesses: (list of 2 strings)
    - suggested_fix: (one sentence on how to improve the answer)
    """

    try:
        response = model.generate_content(prompt)
        # Clean potential markdown formatting from AI response
        clean_json = response.text.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(clean_json)
    except Exception as e:
        return {"error": f"Gemini content analysis failed: {str(e)}"}

if __name__ == "__main__":
    # Test execution
    test_path = "data/test_audio.wav"
    if os.path.exists(test_path):
        result = get_comprehensive_feedback(test_path)
        print(json.dumps(result, indent=2))
    else:
        print(f"File not found: {test_path}")