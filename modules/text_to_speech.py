import os
import wave
import sys

# Adds the parent directory to the system path so it can find config.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google import genai
from google.genai import types
from config import Config

class TextToSpeech:
    def __init__(self):
        self.client = genai.Client(
            api_key=Config.GEMINI_API_KEY
        )

    def generate_audio(self, text, question_number):
        """
        Converts text to speech using Gemini 2.5 and saves it as a .wav file.
        """
        output_filename = f"question_{question_number}.wav"
        output_path = os.path.join(Config.QUESTION_AUDIOS_DIR, output_filename)

        # 2026 Gemini 2.5 TTS allows style prompting
        # Options: 'Charon' (Informative), 'Puck' (Upbeat), 'Kore' (Firm)
        config = types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name='Erinome' 
                    )
                )
            )
        )

        # Style prompt: Tell the AI how to sound
        style_prompt = f"In a professional, clear, and slightly inquisitive tone, ask: {text}"

        try:
            print(f"Generating audio for: {text[:30]}...")
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-preview-tts", # Use a model with TTS capabilities
                contents=style_prompt,
                config=config
            )

            # Save the PCM data to a WAV file
            with wave.open(output_path, "wb") as wf:
                wf.setnchannels(1)       # Mono
                wf.setsampwidth(2)      # 16-bit
                wf.setframerate(24000)  # Gemini standard rate
                wf.writeframes(response.candidates[0].content.parts[0].inline_data.data)
                
            return output_path

        except Exception as e:
            print(f"TTS Error: {e}")
            return None

    def play_audio(self, file_path):
        """Simple helper to play the generated wav file to the user."""
        if os.name == 'nt': # Windows
            os.system(f"start {file_path}")
        else: # Mac/Linux
            os.system(f"afplay {file_path}")

if __name__ == "__main__":
    voice = TextToSpeech()
    print("Generating voice...")
    res = voice.generate_audio("What is your name?", 1)
    if res:
        voice.play_audio(res)
    print(1)   