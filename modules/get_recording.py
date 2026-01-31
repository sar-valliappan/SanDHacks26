import wave
import sys
import os

# Adds the parent directory to the system path so it can find config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import threading
import time
import cv2 as cv
import pyaudio
from config import Config

class InterviewRecorder:
    def __init__(self):
        self.is_recording = False
        self.audio_frames = []
        
        # Audio Settings
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk = 1024
        self.audio_interface = pyaudio.PyAudio()

    def _audio_thread_worker(self, audio_filename):
        """Background task to capture audio chunks."""
        stream = self.audio_interface.open(
            format=self.format, channels=self.channels,
            rate=self.rate, input=True,
            frames_per_buffer=self.chunk
        )
        self.audio_frames = []
        
        while self.is_recording:
            data = stream.read(self.chunk, exception_on_overflow=False)
            self.audio_frames.append(data)
            
        stream.stop_stream()
        stream.close()

        # Save the audio file
        with wave.open(audio_filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio_interface.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(self.audio_frames))

    def record_interview_part(self, video_path, audio_path, duration=60):
        """Starts both video and audio recording simultaneously."""
        cap = cv2.VideoCapture(0)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(video_path, fourcc, 20.0, (640, 480))

        self.is_recording = True
        
        # Start Audio Thread
        audio_thread = threading.Thread(target=self._audio_thread_worker, args=(audio_path,))
        audio_thread.start()

        start_time = time.time()
        print("🔴 Recording... Press 'q' to stop.")

        while self.is_recording:
            ret, frame = cap.read()
            if not ret: break
            
            out.write(frame)
            cv2.imshow('Interview in Progress', frame)

            # Stop triggers
            if (cv2.waitKey(1) & 0xFF == ord('q')) or (time.time() - start_time > duration):
                self.is_recording = False

        # Cleanup
        audio_thread.join() # Wait for audio to finish saving
        cap.release()
        out.release()
        cv2.destroyAllWindows()