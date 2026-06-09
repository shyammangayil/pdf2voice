from typing import Protocol
from core.models import Chunk, AudioSegment

class TTSProvider(Protocol):
    def synthesize(self, chunk: Chunk, output_dir: str) -> AudioSegment: ...