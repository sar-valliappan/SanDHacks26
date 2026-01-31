import os
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

class Config:
    # --- API KEYS ---
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    EYEPOP_API_KEY = os.getenv("EYEPOP_API_KEY")
    EYEPOP_POP_ID = os.getenv("EYEPOP_POP_ID")  # The specific 'Pop' you created in the dashboard
    WISPR_FLOW_API_KEY = os.getenv("WISPR_FLOW_API_KEY")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_REGION = "us-west2" 

    # --- MODEL SETTINGS ---
    # Gemini configurations
    GEMINI_MODEL_NAME = "gemini-2.5-flash"
    TEMPERATURE = 0.7
    MAX_OUTPUT_TOKENS = 2048
    MAX_QUESTIONS = 5
    
    # --- FILE SYSTEM PATHS ---
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    ANSWER_AUDIOS_DIR = os.path.join(DATA_DIR, "answer_audios")
    ANSWER_VIDEOS_DIR = os.path.join(DATA_DIR, "answer_videos")
    QUESTION_AUDIOS_DIR = os.path.join(DATA_DIR, "question_audios")

    # Ensure directories exist
    for _dir in [DATA_DIR, ANSWER_AUDIOS_DIR, ANSWER_VIDEOS_DIR, QUESTION_AUDIOS_DIR]:
        if not os.path.exists(_dir):
            os.makedirs(_dir)