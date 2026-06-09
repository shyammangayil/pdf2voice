import yaml
from dataclasses import dataclass

@dataclass
class AppConfig:
    ocr_engine: str = "paddle"
    tts_engine: str = "kokoro"
    chunk_size: int = 1000
    fps: int = 1
    output_format: str = "mp4"
    output_dir: str = "./output"

    @classmethod
    def load(cls, path: str = "config.yaml") -> "AppConfig":
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                return cls(**data)
        except FileNotFoundError:
            return cls()