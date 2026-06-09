import fitz
import os
from typing import Protocol
from core.models import Book, Chapter, Page, Paragraph

class OCRProvider(Protocol):
    def extract(self, image_path: str) -> str: ...

class OCRExtractor:
    def __init__(self, ocr_provider: OCRProvider, output_dir: str):
        self.ocr_provider = ocr_provider
        self.output_dir = output_dir

    def extract(self, pdf_path: str) -> Book:
        doc = fitz.open(pdf_path)
        chapters = [Chapter(chapter_id="ch_1", title="Main Content")]

        for i, page in enumerate(doc):
            img_path = os.path.join(self.output_dir, f"page_{i+1:03d}.png")
            pix = page.get_pixmap(dpi=300) # Higher DPI for OCR
            pix.save(img_path)

            raw_text = self.ocr_provider.extract(img_path)
            paragraphs = [Paragraph(p.strip()) for p in raw_text.split('\n\n') if p.strip()]
            chapters[0].pages.append(Page(page_number=i+1, image_path=img_path, paragraphs=paragraphs))

        return Book(title=os.path.basename(pdf_path), chapters=chapters)