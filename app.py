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
from tts.gtts_provider import GTTSProvider
from tts.edge_tts_provider import EdgeTTSProvider
from timeline.timeline_builder import TimelineBuilder
from renderers.ffmpeg_renderer import FFmpegRenderer

# Registry of available TTS providers.
# Add new providers here — no other file needs to change.
TTS_PROVIDERS = {
    "edge":   lambda: EdgeTTSProvider(),
    "gtts":   lambda: GTTSProvider(),
    "kokoro": lambda: KokoroTTSProvider(),
}


def setup_container(config: AppConfig, output_dir: str) -> ServiceContainer:
    container = ServiceContainer()

    # Extractors
    container.register("digital_extractor", DigitalPdfExtractor(output_dir))

    class MockPaddleOCR:
        def extract(self, img_path): return "Mocked OCR Text"
    container.register("ocr_extractor", OCRExtractor(MockPaddleOCR(), output_dir))

    # TTS — resolved from config; CLI --tts flag overwrites config.yaml value
    provider_key = config.tts_engine.lower()
    if provider_key not in TTS_PROVIDERS:
        raise ValueError(
            f"Unknown TTS engine '{provider_key}'. "
            f"Available: {', '.join(TTS_PROVIDERS)}"
        )
    container.register("tts", TTS_PROVIDERS[provider_key]())

    # Other components
    container.register("cleaner", TextCleaner())
    container.register("chunker", ChapterChunker(max_words=config.chunk_size))
    container.register("timeline_builder", TimelineBuilder())
    container.register("renderer", FFmpegRenderer(fps=config.fps))

    return container


@click.command()
@click.argument("input_pdf", type=click.Path(exists=True))
@click.option("--ocr", default=None, help="OCR engine to use if scanned (overrides config.yaml)")
@click.option(
    "--tts", default=None,
    type=click.Choice(list(TTS_PROVIDERS), case_sensitive=False),
    help=f"TTS engine. Choices: {', '.join(TTS_PROVIDERS)}. Overrides config.yaml.",
)
@click.option("--chunk-size", default=None, type=int, help="Max words per chunk (overrides config.yaml)")
@click.option("--output", default="output.mp4", help="Output MP4 path")
def main(input_pdf, ocr, tts, chunk_size, output):
    config = AppConfig.load()

    # CLI flags override config.yaml when explicitly provided
    if tts:
        config.tts_engine = tts
    if ocr:
        config.ocr_engine = ocr
    if chunk_size is not None:
        config.chunk_size = chunk_size

    output_dir = os.path.dirname(os.path.abspath(output)) or "."
    os.makedirs(output_dir, exist_ok=True)

    container = setup_container(config, output_dir)

    click.echo(f"Processing : {input_pdf}")
    click.echo(f"TTS engine : {config.tts_engine}")
    click.echo(f"Chunk size : {config.chunk_size} words")

    # 1. Detect
    is_scanned = DocumentDetector.is_scanned(input_pdf)
    click.echo(f"Doc type   : {'Scanned' if is_scanned else 'Digital'}")

    # 2. Extract
    extractor = container.resolve("ocr_extractor") if is_scanned else container.resolve("digital_extractor")
    book = extractor.extract(input_pdf)
    click.echo(f"Extracted  : {sum(len(ch.pages) for ch in book.chapters)} pages")

    # 3. Clean
    cleaner = container.resolve("cleaner")
    book = cleaner.clean(book)

    # 4. Chunk
    chunker = container.resolve("chunker")
    chunks = chunker.create_chunks(book)
    click.echo(f"Chunks     : {len(chunks)}")

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
