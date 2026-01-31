import time
import os
import cv2
import sys

# Adds the parent directory to the system path so it can find config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.gen_questions import QuestionGenerator
from modules.text_to_speech import TextToSpeech
from modules.get_recording import InterviewRecorder
from config import Config

def run_countdown(seconds):
    """Displays a simple terminal countdown for preparation."""
    print(f"\n⏱️ Get ready! You have {seconds} seconds to prepare...")
    for i in range(seconds, 0, -1):
        print(f"\rStarting in {i}... ", end="", flush=True)
        time.sleep(1)
    print("\n🎬 RECORDING STARTED! (Press 'q' to finish early)\n")

def start_interview():
    # Initialize components
    q_gen = QuestionGenerator()
    tts = TextToSpeech()
    recorder = InterviewRecorder()

    # 1. Inputs: Resume and Job Description
    print("--- 🤖 AI Interview Coach: Setup ---")
    resume_path = input("Enter the path to your Resume PDF (e.g., ~/data/resume.pdf): ")
    jd_text = input("Paste the Job Description here: \n")

    # 2. Generate Questions using Gemini
    print("\n🧠 AI is analyzing your profile and the job role...")
    # Assume generate_questions returns a list of strings
    q_gen.generate_interview_questions(jd_text, resume_path)
    questions = os.path.join(Config.DATA_DIR, "questions.json").get("questions")

    if not questions:
        print("❌ Failed to generate questions. Check your API key or inputs.")
        return

    print(f"✅ Generated {len(questions)} questions. Let's begin!\n")

    # 3. Main Loop
    for i, question in enumerate(questions):
        print(f"--- Question {i+1} ---")
        print(f"Question: {question}")
        
        # A. Speaking and Displaying the Question
        # speak_question handles the TTS and returns the path to the .wav
        audio_file = tts.generate_audio(question, i)
        
        # B. Wait for TTS to finish (or use a non-blocking play if preferred)
        tts.play_audio(audio_file)
        
        # C. 10-second Preparation Countdown
        run_countdown(10)
        
        # D. Record Answer (Video + Audio)
        video_output = os.path.join(Config.DATA_DIR, f"answer_video_{i}.mp4")
        audio_output = os.path.join(Config.DATA_DIR, f"answer_audio_{i}.wav")
        
        # record handles both streams via threading
        recorder.record(video_output, audio_output, duration=5)
        
        print(f"✅ Answer {i+1} recorded and saved.\n")
        time.sleep(2) # Brief pause before the next question

    print("🎉 Interview Complete! All recordings are stored in the data folder.")

if __name__ == "__main__":
    start_interview()