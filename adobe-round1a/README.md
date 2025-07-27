# PDF Outline Extractor - Adobe "Connecting the Dots" Hackathon (TEAM- DP28)

**Fast, offline, CPU-only solution** for extracting structured outlines from PDF documents and outputting them as JSON files.

## Key Features

- ✅ **Fully offline** - No internet access required
- ⚡ **High performance** - Completes within 10 seconds for 50-page PDFs
- 🖥️ **CPU-only processing** - No GPU dependencies
- 🐳 **Dockerizable** - Ready for containerized deployment
- 🧠 **Smart heuristics** - Uses font size, boldness, positioning for heading detection
- 📊 **Modular design** - Clean separation of concerns

## Requirements Met

- Model size: <200MB (only PyMuPDF ~50MB)
- Processing time: <10s for 50-page PDFs
- Network isolation: `--network none` compatible
- Heuristic-based heading detection
- No hardcoded document-specific logic

## Quick Start

### Docker Deployment (Recommended)

1. **Build the Docker image:**
```bash
./build.sh
# OR manually:
docker build -t mysolution:tag .
```

2. **Run with your PDFs:**
```bash
docker run --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output --network none mysolution:tag
```

### Local Development

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Run locally:**
```bash
mkdir input output
# Place PDF files in input/
python pdf_outline_extractor.py
```

## Output Format

For each input PDF, generates a JSON file with this structure:
```json
{
  "title": "Understanding AI",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "What is AI?", "page": 2 },
    { "level": "H3", "text": "History of AI", "page": 3 }
  ]
}
```

## Algorithm Overview

### Modular Architecture
- `detect_title()` - Finds largest font at top of page 1
- `extract_headings()` - Uses statistical font analysis for heading detection
- `write_output_json()` - Outputs structured JSON

### Heading Detection Heuristics
1. **Font Size Analysis**: Statistical comparison against document median
2. **Bold Text Detection**: Weighted scoring for bold formatting
3. **Position Analysis**: Considers vertical positioning and whitespace
4. **Pattern Recognition**: Numbered headings, uppercase text
5. **Scoring System**: Multi-factor classification (H1/H2/H3)

### Performance Optimizations
- Limits processing to 50 pages max
- Processes max 100 blocks per page
- Two-pass algorithm: statistics collection → heading extraction
- Duplicate text filtering
- Early termination for speed

## Technical Specifications

- **Library**: PyMuPDF (fitz) only - ~50MB
- **Processing**: CPU-only, no external dependencies
- **Memory**: Optimized for large documents
- **Speed**: <10s for 50-page PDFs
- **Compatibility**: Works with various PDF formats and styles

## File Structure
```
├── pdf_outline_extractor.py  # Main extraction logic
├── requirements.txt          # PyMuPDF dependency
├── Dockerfile               # Container configuration
├── build.sh                 # Build script
└── README.md               # This file
```
