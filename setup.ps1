
---

### 2. `setup.ps1`
Save this in the root directory (`E:\src\pdf2voice\setup.ps1`). This script automates the environment setup, checks for FFmpeg, and creates the necessary folders.

```powershell
# PDF-to-Audiobook-MP4 Setup Script
# Run this in PowerShell: .\setup.ps1

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "    [OK] $Message" -ForegroundColor Green
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "    [!] $Message" -ForegroundColor Yellow
}

Write-Host "==================================================" -ForegroundColor Magenta
Write-Host "  PDF-to-Audiobook-MP4 System Setup" -ForegroundColor Magenta
Write-Host "==================================================" -ForegroundColor Magenta

# 1. Check Python Version
Write-Step "Checking Python version..."
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python 3\.(1[2-9]|[2-9][0-9])") {
    Write-Success "Found $pythonVersion"
} else {
    Write-Warning-Custom "Python 3.12+ is recommended. Found: $pythonVersion"
}

# 2. Check FFmpeg
Write-Step "Checking for FFmpeg..."
try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Success "FFmpeg is installed: $ffmpegVersion"
} catch {
    Write-Warning-Custom "FFmpeg not found in PATH!"
    Write-Host "    Please install FFmpeg and add it to your system PATH." -ForegroundColor Red
    Write-Host "    Download: https://www.gyan.dev/ffmpeg/builds/" -ForegroundColor Red
    exit 1
}

# 3. Create Virtual Environment
Write-Step "Setting up Python Virtual Environment..."
if (Test-Path ".venv") {
    Write-Success "Virtual environment '.venv' already exists."
} else {
    python -m venv .venv
    Write-Success "Virtual environment created."
}

# 4. Activate Virtual Environment
Write-Step "Activating virtual environment..."
& ".\.venv\Scripts\Activate.ps1"
Write-Success "Environment activated."

# 5. Install Dependencies
Write-Step "Installing dependencies from requirements.txt..."
if (Test-Path "requirements.txt") {
    pip install --upgrade pip
    pip install -r requirements.txt
    Write-Success "Dependencies installed successfully."
} else {
    Write-Warning-Custom "requirements.txt not found. Skipping pip install."
}

# 6. Create Required Directories
Write-Step "Creating project directories..."
$dirs = @("samples", "output", "tests")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Success "Created directory: $dir/"
    } else {
        Write-Success "Directory already exists: $dir/"
    }
}

# 7. Create default config if missing
if (-not (Test-Path "config.yaml")) {
    Write-Step "Creating default config.yaml..."
    $configContent = @"
ocr_engine: paddle
tts_engine: gtts
chunk_size: 1000
fps: 1
output_format: mp4
output_dir: "./output"
"@
    Set-Content -Path "config.yaml" -Value $configContent
    Write-Success "Created config.yaml"
}

Write-Host "`n==================================================" -ForegroundColor Magenta
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Magenta
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Place a test PDF in the 'samples/' folder."
Write-Host "2. Run: python app.py samples/your_file.pdf --output output/test.mp4"
Write-Host ""