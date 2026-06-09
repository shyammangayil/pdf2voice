import os
import click
from utils.config import AppConfig
from utils.di import ServiceContainer
from extractors.detector import DocumentDetector
from extractors.pymupdf_extractor import DigitalPdfExtractor
from extractors.ocr_extractor import OCRExtractor
from cleaners.text_cleaner import TextCleaner
from chunkers.chapter_chunker import ChapterChunker
from tts.kokoro_tts import KokoroTTSProvider
from timeline.timeline_builder import TimelineBuilder
from renderers.ffmpeg_renderer import FFmpegRenderer
from tts.gtts_provider import GTTSProvider

def setup_container(config: AppConfig, output_dir: str) -> ServiceContainer:
    container = ServiceContainer()
    
    # Register Extractors
    container.register("digital_extractor", DigitalPdfExtractor(output_dir))
    
    # Register OCR Provider (Mocked for structure, would import PaddleOCR here)
    class MockPaddleOCR:
        def extract(self, img_path): return "Mocked OCR Text"
    container.register("ocr_extractor", OCRExtractor(MockPaddleOCR(), output_dir))
    
    # Register TTS
    container.register("tts", GTTSProvider())
    
    # Register Components
    container.register("cleaner", TextCleaner())
    container.register("chunker", ChapterChunker(max_words=config.chunk_size))
    container.register("timeline_builder", TimelineBuilder())
    container.register("renderer", FFmpegRenderer(fps=config.fps))
    
    return container

@click.command()
@click.argument('input_pdf', type=click.Path(exists=True))
@click.option('--ocr', default='paddle', help='OCR engine to use if scanned')
@click.option('--tts', default='kokoro', help='TTS engine to use')
@click.option('--chunk-size', default=1000, help='Max words per chunk')
@click.option('--output', default='output.mp4', help='Output MP4 path')
def main(input_pdf, ocr, tts, chunk_size, output):
    config = AppConfig.load()
    config.chunk_size = chunk_size
    
    output_dir = os.path.dirname(os.path.abspath(output)) or "."
    os.makedirs(output_dir, exist_ok=True)
    
    container = setup_container(config, output_dir)
    
    click.echo(f"Processing: {input_pdf}")
    
    # 1. Detect
    is_scanned = DocumentDetector.is_scanned(input_pdf)
    click.echo(f"Document type: {'Scanned' if is_scanned else 'Digital'}")
    
    # 2. Extract
    extractor = container.resolve("ocr_extractor") if is_scanned else container.resolve("digital_extractor")
    book = extractor.extract(input_pdf)
    click.echo(f"Extracted {sum(len(ch.pages) for ch in book.chapters)} pages.")
    
    # 3. Clean
    cleaner = container.resolve("cleaner")
    book = cleaner.clean(book)
    
    # 4. Chunk
    chunker = container.resolve("chunker")
    chunks = chunker.create_chunks(book)
    click.echo(f"Created {len(chunks)} chunks.")
    
    # 5. Synthesize Audio
    tts_engine = container.resolve("tts")
    audio_segments = []
    for chunk in chunks:
        click.echo(f"Synthesizing {chunk.chunk_id}...")
        segment = tts_engine.synthesize(chunk, output_dir)
        audio_segments.append(segment)
        
    # 6. Build Timeline
    timeline_builder = container.resolve("timeline_builder")
    timeline = timeline_builder.build(book, chunks, audio_segments)
    
    # 7. Render
    click.echo("Rendering MP4...")
    renderer = container.resolve("renderer")
    renderer.render(timeline, output)
    
    click.echo(f"Success! Output saved to: {output}")

if __name__ == "__main__":
    main()