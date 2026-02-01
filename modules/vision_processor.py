
import os
import sys
import json
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()


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
        print(f"[INFO] Waiting for file... ({file_status.state.name})")
        time.sleep(2)
    return False


class VisionProcessor:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
    
    def analyze_video(self, video_path: str) -> dict:
        """Analyze video for eye contact, expressions, confidence."""
        if not os.path.exists(video_path):
            return {"error": f"Video not found: {video_path}"}
        
        if not self.api_key:
            return {"error": "GEMINI_API_KEY not configured"}
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            print(f"[INFO] Uploading video for vision analysis...")
            video_file = genai.upload_file(video_path)
            
            # Wait for file to become active
            if not wait_for_file_active(video_file):
                return {"error": "Video upload failed - file not ready"}
            
            print("[INFO] Video ready, analyzing...")
            model = genai.GenerativeModel("gemini-2.0-flash")
            
            response = model.generate_content([
                """Watch this video and analyze the person's visual presentation. Return a JSON object:
                - eye_contact: description of eye contact (e.g., "Maintained good eye contact with camera", "Frequently looked away")
                - looking_away_frequency: "rarely", "sometimes", or "frequently"
                - facial_expressions: what you observe (e.g., "Appeared confident and engaged", "Seemed nervous")
                - confidence_visual: "high", "medium", or "low"
                - body_language: brief description
                - fidgeting: "none", "minimal", "noticeable", or "excessive"
                - interest_level: "very engaged", "engaged", "neutral", or "disengaged"
                - overall_impression: 1-2 sentence summary
                
                Return ONLY valid JSON, no markdown.""",
                video_file
            ])
            
            try:
                video_file.delete()
            except:
                pass
            
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            
            result = json.loads(text)
            print(f"[INFO] Vision analysis complete")
            return result
            
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse vision response")
            return {
                "eye_contact": "Could not analyze",
                "confidence_visual": "medium",
                "looking_away_frequency": "unknown",
                "overall_impression": "Analysis incomplete"
            }
        except Exception as e:
            print(f"[ERROR] Vision analysis failed: {e}")
            return {"error": str(e)}


if __name__ == "__main__":
    processor = VisionProcessor()
    if len(sys.argv) > 1:
        result = processor.analyze_video(sys.argv[1])
        print(json.dumps(result, indent=2))
