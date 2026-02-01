
import json
import os
import sys

# Adds the parent directory to the system path so it can find config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config

class QuestionGenerator:
    def __init__(self):
        pass

    def generate_interview_questions(self, job_description, pdf_path):
        """
        Returns hardcoded mock questions to get the app running.
        """
        print(f"Generating MOCK questions for: {job_description}")
        
        # MOCK DATA - This will always work
        questions_data = {
            "resume_info": {
                "name": "Candidate",
                "skills": ["Python", "JavaScript", "React"],
                "experience_years": 2,
                "keywords": ["full-stack", "web development", "API"]
            },
            "questions": [
                "Tell me about yourself and your background in software development.",
                "Can you describe a challenging project you worked on and how you overcame obstacles?",
                "How do you approach learning new technologies?",
                "Describe your experience with version control and team collaboration.",
                "Where do you see yourself in 5 years?"
            ]
        }
        
        # Save output
        os.makedirs(Config.DATA_DIR, exist_ok=True)
        output_path = os.path.join(Config.DATA_DIR, "questions.json")
        with open(output_path, "w") as f:
            json.dump(questions_data, f, indent=4)
            
        return questions_data

if __name__ == "__main__":
    generator = QuestionGenerator()
    res = generator.generate_interview_questions("Test", "test.pdf")
    print(res)