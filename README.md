# PDF-to-Audiobook-MP4 System

A modular, extensible Python system that converts PDF documents into synchronized MP4 audiobooks. It automatically detects scanned documents, falls back to OCR, cleans text artifacts, and uses Text-to-Speech (TTS) engines to generate narrated video with static page visuals.

## 🌟 Features
- **Smart Detection**: Automatically distinguishes between digital and scanned PDFs.
- **OCR Fallback**: Pluggable OCR support (PaddleOCR, Tesseract, Surya) for scanned documents.
- **Text Cleaning**: Removes page numbers, repeated headers/footers, and fixes hyphenation artifacts.
- **Canonical AST**: A strict, decoupled intermediate representation (`Book`, `Chapter`, `Page`, `Chunk`) ensuring downstream tools never couple directly to PDF extraction.
- **Modular TTS**: Interchangeable TTS providers (Kokoro, Piper, OpenAI, gTTS).
- **Timeline Synchronization**: Proportionally maps audio duration to page visuals based on word count.
- **FFmpeg Rendering**: Compiles images and audio segments into a single, high-quality MP4.

## 🛠️ Prerequisites
1. **Python 3.12+** installed.
2. **FFmpeg** installed and added to your system `PATH`. 
   - *Windows*: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/), extract, and add the `bin` folder to Environment Variables.
   - *Verify*: Run `ffmpeg -version` in your terminal.
3. *(Optional)* **Tesseract OCR** or **PaddleOCR** if you plan to process scanned PDFs.

## 🚀 Quick Start

### 1. Automated Setup
Run the provided PowerShell setup script to create the virtual environment and install dependencies:
```powershell
.\setup.ps1