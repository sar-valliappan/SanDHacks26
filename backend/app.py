
import os
import shutil
import uuid
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

import sys
# Add parent directory to path to find modules and config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from modules.gen_questions import QuestionGenerator
from modules.text_to_speech import TextToSpeech
from modules.voice_engine import process_file
from modules.vision_processor import VisionProcessor
from modules.feedback import FeedbackGenerator

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules
question_gen = QuestionGenerator()
tts = TextToSpeech()
vision = VisionProcessor()
feedback_gen = FeedbackGenerator()

# In-memory storage for session data (replace with database in production)
sessions = {}

class InitSessionResponse(BaseModel):
    session_id: str
    questions: List[str]

class AnalysisResponse(BaseModel):
    transcript: str
    voice_metrics: dict
    vision_metrics: dict
    feedback: dict

@app.post("/api/interview/init", response_model=InitSessionResponse)
async def init_interview(
    job_description: str = Form(...),
    resume: UploadFile = File(...)
):
    session_id = str(uuid.uuid4())
    
    # Save resume temporarily
    resume_path = os.path.join(Config.DATA_DIR, f"{session_id}_resume.pdf")
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    
    with open(resume_path, "wb") as buffer:
        shutil.copyfileobj(resume.file, buffer)
        
    # Generate questions
    print(f"Generating questions for session {session_id}...")
    try:
        q_data = question_gen.generate_interview_questions(job_description, resume_path)
        questions = q_data.get("questions", [])
        
        sessions[session_id] = {
            "job_description": job_description,
            "resume_path": resume_path,
            "questions": questions,
            "responses": {} 
        }
        
        return {"session_id": session_id, "questions": questions}
    except Exception as e:
        print(f"Error in init_interview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interview/{session_id}/question/{q_index}/audio")
async def get_question_audio(session_id: str, q_index: int):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    questions = sessions[session_id]["questions"]
    if q_index < 0 or q_index >= len(questions):
        raise HTTPException(status_code=404, detail="Question index out of range")
        
    question_text = questions[q_index]
    
    # Check if audio already exists
    audio_path = os.path.join(Config.DATA_DIR, f"{session_id}_q{q_index}.wav")
    if not os.path.exists(audio_path):
        # Generate it
        print(f"Generating audio for q{q_index}...")
        generated_path = tts.generate_audio(question_text, f"{session_id}_q{q_index}")
        if not generated_path:
             raise HTTPException(status_code=500, detail="TTS Generation failed")
        # tts.generate_audio saves to predictable name, we might need to rename if logic differs
        # The current tts.generate_audio saves to `question_{number}.wav` in DATA_DIR
        # Use a custom modified version or rename
        # For now, let's assume we modify tts to return the path it saved. 
        # Actually my mock TTS saves to `question_{number}.wav` ignoring session.
        # Let's fix that by renaming the file if needed.
        if generated_path != audio_path:
             if os.path.exists(generated_path):
                 os.rename(generated_path, audio_path)
    
    return FileResponse(audio_path, media_type="audio/wav")

@app.post("/api/interview/{session_id}/response/{q_index}")
async def upload_response(
    session_id: str,
    q_index: int,
    video: UploadFile = File(...),
    duration_seconds: float = Form(0)
):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Save video
    ext = os.path.splitext(video.filename)[1]
    if not ext:
        ext = ".webm"
        
    video_path = os.path.join(Config.DATA_DIR, f"{session_id}_resp_q{q_index}{ext}")
    with open(video_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)
        
    # Store path and duration
    if "responses" not in sessions[session_id]:
         sessions[session_id]["responses"] = {}
         
    sessions[session_id]["responses"][q_index] = {
        "video_path": video_path,
        "duration_seconds": float(duration_seconds) if duration_seconds else 0,
        "analyzed": False
    }
    
    print(f"Received response: {video_path}, duration: {duration_seconds}s")
    return {"status": "received", "path": video_path, "duration": duration_seconds}

@app.post("/api/interview/{session_id}/analyze/{q_index}", response_model=AnalysisResponse)
async def analyze_response(session_id: str, q_index: int):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    response_data = sessions[session_id]["responses"].get(q_index)
    if not response_data:
        raise HTTPException(status_code=404, detail="Response not found")
        
    video_path = response_data["video_path"]
    question_text = sessions[session_id]["questions"][q_index]
    actual_duration = response_data.get("duration_seconds", 0)
    
    # 1. Voice Analysis (Transcript + Metrics)
    print(f"Running Voice Analysis... (actual duration: {actual_duration}s)")
    voice_result = process_file(video_path)
    if "error" in voice_result:
        print(f"Voice error: {voice_result['error']}")
    
    # Recalculate metrics using actual duration from frontend
    transcript = voice_result.get("transcript", "")
    metrics = voice_result.get("metrics", {})
    
    if actual_duration > 0 and transcript:
        import re
        words = re.findall(r"\b[\w']+\b", transcript)
        word_count = len(words)
        # WPM = (words / seconds) * 60
        pace_wpm = int(round(word_count / actual_duration * 60)) if actual_duration > 0 else 0
        metrics["word_count"] = word_count
        metrics["duration_seconds"] = actual_duration
        metrics["pace_wpm"] = pace_wpm
        print(f"Recalculated: {word_count} words in {actual_duration}s = {pace_wpm} WPM")
        
    # 2. Vision Analysis
    print("Running Vision Analysis...")
    vision_result = vision.analyze_video(video_path)
    if "error" in vision_result:
        print(f"Vision error: {vision_result['error']}")
        
    # 3. Generate Feedback
    print("Generating Feedback...")
    feedback = feedback_gen.generate_feedback(
        transcript=transcript,
        voice_metrics=metrics,
        vision_metrics=vision_result,
        question=question_text
    )
    
    # Store results
    sessions[session_id]["responses"][q_index]["analysis"] = {
        "voice": voice_result,
        "vision": vision_result,
        "feedback": feedback
    }
    
    return {
        "transcript": transcript,
        "voice_metrics": metrics,
        "vision_metrics": vision_result,
        "feedback": feedback,
        "analysis": voice_result.get("analysis", {})
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
