from core.models import Book, Chunk

class ChapterChunker:
    def __init__(self, max_words: int = 1000):
        self.max_words = max_words

    def create_chunks(self, book: Book) -> list[Chunk]:
        chunks = []
        chunk_counter = 0

        for chapter in book.chapters:
            current_text = ""
            current_pages = []

            for page in chapter.pages:
                current_text += " " + page.text
                current_pages.append(page.page_number)

                # Split if we exceed max_words or at chapter end
                if len(current_text.split()) >= self.max_words or page == chapter.pages[-1]:
                    chunks.append(Chunk(
                        chunk_id=f"chk_{chunk_counter:04d}",
                        chapter_id=chapter.chapter_id,
                        text=current_text.strip(),
                        target_pages=current_pages.copy()
                    ))
                    chunk_counter += 1
                    current_text = ""
                    current_pages = []

        return chunks