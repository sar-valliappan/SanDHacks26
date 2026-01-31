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

    # --- MODEL SETTINGS ---
    # Gemini configurations
    GEMINI_MODEL_NAME = "gemini-1.5-pro"
    TEMPERATURE = 0.7
    MAX_OUTPUT_TOKENS = 2048
    
    # --- FILE SYSTEM PATHS ---
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")