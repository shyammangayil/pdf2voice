import os
import subprocess
import json
import time
from gtts import gTTS
from gtts.tts import gTTSError
from core.models import Chunk, AudioSegment

class GTTSProvider:
    def __init__(self, max_retries=5, initial_delay=5):
        self.max_retries = max_retries
        self.initial_delay = initial_delay

    def synthesize(self, chunk: Chunk, output_dir: str) -> AudioSegment:
        audio_path = os.path.join(output_dir, f"{chunk.chunk_id}.mp3")
        
        # 1. Resume Capability: If file exists and is larger than 1KB, skip generation
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
            print(f"  [Skipping] {chunk.chunk_id} already exists.")
            return self._get_audio_segment(chunk.chunk_id, audio_path)

        retries = 0
        delay = self.initial_delay
        
        # 2. Retry Loop with Exponential Backoff
        while retries < self.max_retries:
            try:
                tts = gTTS(text=chunk.text, lang='en')
                tts.save(audio_path)
                
                # 3. Be Polite: Wait 1 second before the next chunk to avoid rate limits
                time.sleep(1) 
                break # Success! Exit the retry loop
                
            except gTTSError as e:
                if "429" in str(e) or "Too Many Requests" in str(e):
                    retries += 1
                    print(f"\n⚠️ Rate limit hit (429). Waiting {delay} seconds before retry {retries}/{self.max_retries}...")
                    time.sleep(delay)
                    delay *= 2 # Exponential backoff (5s, 10s, 20s, 40s...)
                else:
                    raise e # If it's a different error (e.g., no internet), crash normally
        else:
            raise RuntimeError(f"Failed to synthesize {chunk.chunk_id} after {self.max_retries} retries due to rate limiting.")

        return self._get_audio_segment(chunk.chunk_id, audio_path)

    def _get_audio_segment(self, chunk_id, audio_path):
        # Get exact duration using ffprobe for perfect sync
        cmd = [
            "ffprobe", "-v", "quiet", "-print_format", "json", 
            "-show_format", audio_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        duration = 1.0
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                duration = float(data['format']['duration'])
            except (KeyError, ValueError, json.JSONDecodeError):
                pass
                
        return AudioSegment(chunk_id=chunk_id, file_path=audio_path, duration=duration)