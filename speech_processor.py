# speech_processor.py - Using faster-whisper
from faster_whisper import WhisperModel
import tempfile
import os
from typing import Optional

class SpeechProcessor:
    def __init__(self):
        print("Loading Faster-Whisper model...")
        try:
            # Use faster-whisper (more memory efficient)
            self.model = WhisperModel("base", device="cpu", compute_type="int8")
            print("Faster-Whisper model loaded successfully!")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            self.model = None
        
    async def speech_to_text(self, audio_data: bytes) -> Optional[str]:
        """Convert speech audio to text using Faster-Whisper"""
        if not self.model:
            print("Whisper model not loaded")
            return None
            
        try:
            print("Starting speech recognition with Faster-Whisper...")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio.write(audio_data)
                temp_path = temp_audio.name
            
            try:
                # Transcribe using faster-whisper
                segments, info = self.model.transcribe(temp_path)
                
                # Combine all segments
                transcribed_text = " ".join(segment.text for segment in segments).strip()
                
                print(f"Faster-Whisper transcription: '{transcribed_text}'")
                print(f"Language: {info.language}, Probability: {info.language_probability}")
                
                if transcribed_text and len(transcribed_text) > 3:
                    return transcribed_text
                else:
                    print("Transcription too short or empty")
                    return None
                    
            finally:
                # Clean up
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            
        except Exception as e:
            print(f"Error in speech to text: {e}")
            return None