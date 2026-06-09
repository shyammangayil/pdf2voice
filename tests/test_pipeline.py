import os
import pytest
from core.models import Book, Chapter, Page, Paragraph, Chunk
from cleaners.text_cleaner import TextCleaner
from chunkers.chapter_chunker import ChapterChunker

def test_text_cleaner_hyphenation():
    cleaner = TextCleaner()
    book = Book(title="Test", chapters=[
        Chapter(chapter_id="1", title="Ch1", pages=[
            Page(page_number=1, paragraphs=[Paragraph("infor-\nmation technology")])
        ])
    ])
    cleaned = cleaner.clean(book)
    assert "information technology" in cleaned.chapters[0].pages[0].text

def test_chunker_splits_by_size():
    chunker = ChapterChunker(max_words=5)
    book = Book(title="Test", chapters=[
        Chapter(chapter_id="1", title="Ch1", pages=[
            Page(page_number=1, paragraphs=[Paragraph("one two three four five six seven")])
        ])
    ])
    chunks = chunker.create_chunks(book)
    assert len(chunks) >= 2
    assert len(chunks[0].text.split()) <= 5