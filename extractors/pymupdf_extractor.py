import fitz  # PyMuPDF
import os
from core.models import Book, Chapter, Page, Paragraph
from extractors.base import Extractor

class DigitalPdfExtractor:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def extract(self, pdf_path: str) -> Book:
        doc = fitz.open(pdf_path)
        chapters = [Chapter(chapter_id="ch_1", title="Main Content")]
        
        for i, page in enumerate(doc):
            text = page.get_text().strip()
            if not text:
                continue
                
            # Extract image
            img_path = os.path.join(self.output_dir, f"page_{i+1:03d}.png")
            pix = page.get_pixmap(dpi=150)
            pix.save(img_path)

            paragraphs = [Paragraph(p.strip()) for p in text.split('\n\n') if p.strip()]
            chapters[0].pages.append(Page(page_number=i+1, image_path=img_path, paragraphs=paragraphs))
            
        return Book(title=os.path.basename(pdf_path), chapters=chapters)