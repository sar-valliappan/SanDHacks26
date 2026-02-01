
import os
import sys
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

class FeedbackGenerator:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
    
    def generate_feedback(self, transcript: str, voice_metrics: dict, vision_metrics: dict, question: str) -> dict:
        """
        Generate specific, actionable feedback based on the actual response.
        """
        if not self.api_key:
            return {"error": "GEMINI_API_KEY not configured"}
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            model = genai.GenerativeModel("gemini-2.0-flash")
            
            prompt = f"""You are an expert interview coach analyzing a candidate's response.

INTERVIEW QUESTION:
"{question}"

CANDIDATE'S RESPONSE (transcript):
"{transcript}"

VOICE METRICS:
- Words per minute: {voice_metrics.get('pace_wpm', 'N/A')}
- Total filler words used: {voice_metrics.get('total_fillers', 0)}
- Specific fillers: {json.dumps(voice_metrics.get('filler_words', {}))}
- Number of pauses: {voice_metrics.get('pause_count', 0)}
- Response duration: {voice_metrics.get('duration_seconds', 'N/A')} seconds

VISUAL OBSERVATIONS:
- Eye contact: {vision_metrics.get('eye_contact', 'N/A')}
- Confidence (visual): {vision_metrics.get('confidence_visual', 'N/A')}
- Body language: {vision_metrics.get('body_language', 'N/A')}

Provide detailed, specific feedback. Return a JSON object with:
- score: integer 0-100 based on overall performance
- strengths: array of 2-3 specific things they did well (reference actual content from their answer)
- improvements: array of 2-3 specific, actionable improvements (be specific about WHAT to change)
- content_feedback: how well did they answer the question? What was missing?
- delivery_feedback: how was their speaking pace, clarity, confidence?
- improved_answer_suggestion: one specific sentence or phrase they could have said better, with the improved version
- follow_up_question: a likely follow-up question an interviewer would ask based on their answer

Return ONLY valid JSON, no markdown."""

            print("[INFO] Generating feedback...")
            response = model.generate_content(prompt)
            
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            
            result = json.loads(text)
            
            # Ensure required fields
            if "summary" not in result:
                result["summary"] = result.get("content_feedback", "") + " " + result.get("delivery_feedback", "")
            if "strengths" not in result:
                result["strengths"] = ["Response provided"]
            if "improvements" not in result:
                result["improvements"] = ["Continue practicing"]
            if "score" not in result:
                result["score"] = 70
                
            print("[INFO] Feedback generated successfully")
            return result
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse feedback: {e}")
            return {
                "score": 65,
                "strengths": ["Completed the response"],
                "improvements": ["Could not fully analyze - try again"],
                "summary": "Analysis encountered an issue parsing the response."
            }
        except Exception as e:
            print(f"[ERROR] Feedback generation failed: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e), "score": 50, "strengths": [], "improvements": []}


if __name__ == "__main__":
    gen = FeedbackGenerator()
    result = gen.generate_feedback(
        "I have experience with Python and I like working on projects.",
        {"pace_wpm": 120, "filler_words": {"um": 2}, "pause_count": 1},
        {"eye_contact": "Good"},
        "Tell me about your programming experience."
    )
    print(json.dumps(result, indent=2))
