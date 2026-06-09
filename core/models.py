from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Paragraph:
    text: str

@dataclass
class Page:
    page_number: int
    image_path: Optional[str] = None
    paragraphs: List[Paragraph] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(p.text for p in self.paragraphs)

    @property
    def word_count(self) -> int:
        return len(self.text.split())

@dataclass
class Chapter:
    chapter_id: str
    title: str
    pages: List[Page] = field(default_factory=list)

@dataclass
class Book:
    title: str
    chapters: List[Chapter] = field(default_factory=list)

@dataclass
class Chunk:
    chunk_id: str
    chapter_id: str
    text: str
    target_pages: List[int] = field(default_factory=list) # For timeline mapping

@dataclass
class AudioSegment:
    chunk_id: str
    file_path: str
    duration: float # in seconds

@dataclass
class TimelineClip:
    page_number: int
    image_path: str
    start_time: float
    end_time: float
    audio_path: str = ""                 # <-- ADD THIS
    audio_start_offset: float = 0.0      # <-- ADD THIS


@dataclass
class Timeline:
    clips: List[TimelineClip] = field(default_factory=list)