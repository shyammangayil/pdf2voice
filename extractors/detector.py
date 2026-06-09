import fitz

class DocumentDetector:
    @staticmethod
    def is_scanned(pdf_path: str, threshold: int =50) -> bool:
        doc = fitz.open(pdf_path)
        # Check first 3 pages
        for i in range(min(3, len(doc))):
            text = doc[i].get_text().strip()
            if len(text) > threshold:
                return False
        return True