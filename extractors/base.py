from typing import Protocol
from core.models import Book

class Extractor(Protocol):
    def extract(self, pdf_path: str) -> Book: ...