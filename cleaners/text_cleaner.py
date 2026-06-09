import re
from core.models import Book, Paragraph

class TextCleaner:
    def clean(self, book: Book) -> Book:
        for chapter in book.chapters:
            prev_page_text = ""
            for page in chapter.pages:
                cleaned_paragraphs = []
                for p in page.paragraphs:
                    text = p.text
                    # 1. Fix hyphenation across lines
                    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
                    # 2. Join broken lines within a paragraph
                    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
                    # 3. Remove standalone page numbers (heuristic)
                    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
                    
                    cleaned_paragraphs.append(Paragraph(text.strip()))
                
                # 4. Remove repeated headers/footers
                if cleaned_paragraphs:
                    first_p = cleaned_paragraphs[0].text
                    last_p = cleaned_paragraphs[-1].text
                    if first_p in prev_page_text or last_p in prev_page_text:
                        # Simple heuristic: if it matches previous page exactly, it's a header/footer
                        if len(cleaned_paragraphs) > 2:
                            cleaned_paragraphs = cleaned_paragraphs[1:-1]
                            
                page.paragraphs = [p for p in cleaned_paragraphs if p.text]
                prev_page_text = page.text
                
        return book