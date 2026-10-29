import os
import asyncio
import json
import subprocess
import random
import time

from core.models import Chunk, AudioSegment

# Voice options for reference:
# en-US-AriaNeural     — natural, conversational female
# en-US-GuyNeural      — natural male
# en-GB-SoniaNeural    — British female
# en-IN-NeerjaNeural   — Indian English female
# en-IN-PrabhatNeural  — Indian English male
DEFAULT_VOICE = "en-US-AriaNeural"


class EdgeTTSProvider:
    """
    TTS provider backed by Microsoft Edge's read-aloud service via edge-tts.

    Advantages over gTTS:
    - Higher undocumented rate limit (tested stable up to ~200 req/session)
    - No burst detection at normal book-conversion speeds
    - Neural voices (significantly better quality)
    - No API key required

    Limitations:
    - Still unofficial / undocumented endpoint; not suitable for commercial SLAs
    - Requires network access
    - For fully offline use, switch to KokoroTTSProvider or pyttsx3
    """

    def __init__(
        self,
        voice: str = DEFAULT_VOICE,
        max_retries: int = 6,
        initial_delay: float = 3.0,
        inter_request_delay: float = 0.5,
    ):
        self.voice = voice
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.inter_request_delay = inter_request_delay

    # ------------------------------------------------------------------
    # Public interface (matches TTSProvider protocol)
    # ------------------------------------------------------------------

    def synthesize(self, chunk: Chunk, output_dir: str) -> AudioSegment:
        audio_path = os.path.join(output_dir, f"{chunk.chunk_id}.mp3")

        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000:
            print(f"  [Skipping] {chunk.chunk_id} already exists.")
            return self._make_segment(chunk.chunk_id, audio_path)

        self._synthesize_with_retry(chunk.text, audio_path, chunk.chunk_id)

        # Polite inter-request pause — avoids burst detection
        time.sleep(self.inter_request_delay)

        return self._make_segment(chunk.chunk_id, audio_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _synthesize_with_retry(self, text: str, output_path: str, chunk_id: str):
        delay = self.initial_delay

        for attempt in range(1, self.max_retries + 1):
            try:
                asyncio.run(self._async_synthesize(text, output_path))
                return  # success
            except Exception as e:
                is_rate_limit = any(
                    marker in str(e)
                    for marker in ("429", "Too Many Requests", "rate", "throttl")
                )

                if attempt == self.max_retries:
                    raise RuntimeError(
                        f"Failed to synthesize {chunk_id} after {self.max_retries} "
                        f"attempts. Last error: {e}"
                    ) from e

                if is_rate_limit:
                    jittered = delay * random.uniform(0.8, 1.2)
                    print(
                        f"\n⚠️  Rate limit on {chunk_id}. "
                        f"Waiting {jittered:.1f}s (attempt {attempt}/{self.max_retries})..."
                    )
                    time.sleep(jittered)
                    delay *= 2
                else:
                    # Non-rate-limit errors (network blip, malformed text):
                    # short fixed wait then retry once; crash on second failure
                    print(f"\n⚠️  Non-rate error on {chunk_id}: {e}. Retrying in 2s...")
                    time.sleep(2.0)

    async def _async_synthesize(self, text: str, output_path: str):
        try:
            import edge_tts
        except ImportError as exc:
            raise ImportError(
                "edge-tts is not installed. Run: pip install edge-tts"
            ) from exc

        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_path)

    def _make_segment(self, chunk_id: str, audio_path: str) -> AudioSegment:
        duration = self._probe_duration(audio_path)
        return AudioSegment(chunk_id=chunk_id, file_path=audio_path, duration=duration)

    @staticmethod
    def _probe_duration(audio_path: str) -> float:
        """Use ffprobe for exact duration; fall back to estimation."""
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", audio_path,
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return float(data["format"]["duration"])
        except Exception:
            pass
        return 1.0  # safe fallback; timeline proportions still work
