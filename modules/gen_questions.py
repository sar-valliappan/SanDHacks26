import json
import os
import sys

# Adds the parent directory to the system path so it can find config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google import genai
from google.genai import types
from pydantic import BaseModel
from config import Config

class ResumeData(BaseModel):
    candidate_name: str
    email: str
    skills: list[str]
    experience_years: int
    top_keywords: list[str]
    summary: str

class QuestionGenerator:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)

    def generate_interview_questions(self, job_description, pdf_path):
        """
        Analyzes Job Description and Resume to produce tailored interview questions using google-genai.
        """
        # 1. Upload the PDF to the Files API
        print(f"Uploading {pdf_path}...")
        resume_file = self.client.files.upload(file=pdf_path)

        # 2. Define the extraction and generation prompt
        prompt = f"""
        Step 1: Extract the candidate's name, email, skills, and experience from the attached resume PDF.
        Step 2: Compare this resume against the Job Description: {job_description}.
        Step 3: Generate {Config.MAX_QUESTIONS} interview questions and identify key technical keywords.
        """
        # 3. Configure structured output
        # Setting up the response schema for structured JSON output
        config = types.GenerateContentConfig(
            temperature=Config.TEMPERATURE,
            response_mime_type="application/json",
            response_schema={
                "type": "OBJECT",
                "properties": {
                    "resume_info": {
                        "type": "OBJECT",
                        "properties": {
                            "name": {"type": "STRING"},
                            "skills": {"type": "ARRAY", "items": {"type": "STRING"}},
                            "experience_years": {"type": "INTEGER"},
                            "keywords": {"type": "ARRAY", "items": {"type": "STRING"}}
                        }
                    },
                    "questions": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    }
                }
            }
        )

        try:
            response = self.client.models.generate_content(
                model=Config.GEMINI_MODEL_NAME,
                contents=[resume_file, prompt],
                config=config
            )
            
            # Parse the response text as JSON
            questions_data = json.loads(response.text)
            
            # Save output
            output_path = os.path.join(Config.DATA_DIR, "questions.json")
            with open(output_path, "w") as f:
                json.dump(questions_data, f, indent=4)
                
            return questions_data

        except Exception as e:
            print(f"Error generating questions with google-genai: {e}")
            return []

if __name__ == "__main__":
    generator = QuestionGenerator()
    print("Generating questions...")
    # Example logic
    res = generator.generate_interview_questions("Python AI Developer", "data/resumes/SoftwareResume.pdf")
    print(res)