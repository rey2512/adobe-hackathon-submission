#!/usr/bin/env python3
"""
PDF Outline Extractor (Advanced)

A tool for extracting structured outlines (headings) from PDF documents.
Uses PyMuPDF (fitz) for PDF parsing and advanced heuristics based on font
characteristics, text patterns, and position to identify a clean,
hierarchical outline.
"""

import os
import json
import time
import re
import statistics
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import fitz  # PyMuPDF
    Document = fitz.Document
except ImportError:
    print("Missing PyMuPDF library. Install with: pip install PyMuPDF")
    exit(1)

class PDFOutlineExtractor:
    """Extracts structured outlines from PDF documents with advanced heuristics."""

    def __init__(self):
        """Initialize the extractor with refined parameters."""
        self.max_pages_to_analyze = 50

    def _get_font_stats(self, doc: Document) -> Dict[str, float]:
        """Analyzes the document to get statistics about font sizes."""
        all_font_sizes = []
        pages_to_scan = min(len(doc), self.max_pages_to_analyze)
        for page_num in range(pages_to_scan):
            page = doc[page_num]
            blocks = page.get_text("dict").get("blocks", [])
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            if span["text"].strip():
                                all_font_sizes.append(span["size"])
        
        if not all_font_sizes:
            return {"median": 12.0, "p75": 14.0, "p90": 16.0}

        return {
            "median": statistics.median(all_font_sizes),
            "p75": statistics.quantiles(all_font_sizes, n=4)[2], # 75th percentile
            "p90": statistics.quantiles(all_font_sizes, n=10)[8], # 90th percentile
        }

    def detect_title(self, doc: Document) -> str:
        """Detects the main title of the document from the first page."""
        try:
            if doc.metadata and doc.metadata.get('title'):
                title = doc.metadata['title'].strip()
                if title and len(title) > 4 and not title.lower().endswith('.pdf'):
                    return title

            page = doc[0]
            blocks = page.get_text("dict").get("blocks", [])
            candidates = []
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        full_line_text = "".join(s["text"] for s in line["spans"]).strip()
                        if full_line_text and line["spans"]:
                            span = line["spans"][0]
                            if span["bbox"][1] < page.rect.height * 0.4: # Top 40% of page
                                candidates.append({
                                    "text": full_line_text,
                                    "size": span["size"],
                                    "y_pos": span["bbox"][1]
                                })
            
            if candidates:
                candidates.sort(key=lambda x: (-x["size"], x["y_pos"]))
                return candidates[0]["text"]
        except Exception:
            pass
        
        return "Untitled Document"

    def _is_heading(self, line_text: str, font_size: float, font_stats: Dict[str, float]) -> bool:
        """Determines if a line of text is likely a heading."""
        if font_size <= font_stats["median"] * 1.15:
            return False
        
        if not (3 < len(line_text) < 150):
            return False
            
        if re.match(r"^[A-Z]\s*-\s*\d+$", line_text) or re.match(r"^[A-Z]\s*\d+/\d+$", line_text):
            return False
            
        word_count = len(line_text.split())
        if word_count > 10: # Headings are usually concise
            return False
            
        if line_text.endswith('.') and word_count > 5:
            return False
            
        if line_text.strip().startswith('!') or line_text.strip().startswith('*'):
            return False

        return True

    def _classify_heading_level(self, font_size: float, font_stats: Dict[str, float]) -> str:
        """Classifies a heading into H1, H2, or H3 based on font size."""
        if font_size >= font_stats["p90"]:
            return "H1"
        if font_size >= font_stats["p75"]:
            return "H2"
        return "H3"

    def extract_outline(self, pdf_path: str) -> Dict[str, Any]:
        """Extracts the title and a structured outline from a PDF."""
        outline = []
        try:
            doc = fitz.open(pdf_path)
            if len(doc) == 0:
                return {"title": "Empty Document", "outline": []}

            title = self.detect_title(doc)
            font_stats = self._get_font_stats(doc)
            
            pages_to_scan = min(len(doc), self.max_pages_to_analyze)
            seen_headings = set()

            for page_num in range(pages_to_scan):
                page = doc[page_num]
                blocks = page.get_text("dict").get("blocks", [])
                for block in blocks:
                    if "lines" in block:
                        for line in block["lines"]:
                            full_line_text = " ".join(s["text"].strip() for s in line["spans"]).strip()
                            if full_line_text and line["spans"]:
                                span = line["spans"][0]
                                
                                if self._is_heading(full_line_text, span["size"], font_stats):
                                    # Use lowercased text for checking duplicates to be case-insensitive
                                    if full_line_text.lower() not in seen_headings:
                                        level = self._classify_heading_level(span["size"], font_stats)
                                        outline.append({
                                            "level": level,
                                            "text": full_line_text,
                                            "page": page_num + 1
                                        })
                                        seen_headings.add(full_line_text.lower())
            doc.close()
            return {"title": title, "outline": outline}
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")
            return {"title": "Error Processing Document", "outline": []}

def process_directory(input_dir: str, output_dir: str):
    """Processes all PDFs in a directory and saves the outlines as JSON."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    if not input_path.is_dir():
        print(f"Input directory not found: {input_dir}")
        return

    extractor = PDFOutlineExtractor()
    
    for pdf_file in input_path.glob("*.pdf"):
        print(f"Processing {pdf_file.name}...")
        start_time = time.time()
        
        result = extractor.extract_outline(str(pdf_file))
        
        output_filename = pdf_file.stem + ".json"
        output_file_path = output_path / output_filename
        
        try:
            with open(output_file_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            processing_time = time.time() - start_time
            print(f"  > Finished in {processing_time:.2f}s. Output saved to {output_file_path}")
        except Exception as e:
            print(f"  > Error writing JSON for {pdf_file.name}: {e}")

def main():
    """Main entry point for the script."""
    input_dir = os.environ.get("INPUT_DIR", "/app/input")
    output_dir = os.environ.get("OUTPUT_DIR", "/app/output")
    
    if not os.path.exists(input_dir):
        print("Running in local mode. Using './input' and './output' directories.")
        input_dir = "./input"
        output_dir = "./output"
        Path(input_dir).mkdir(exist_ok=True)
        Path(output_dir).mkdir(exist_ok=True)

    process_directory(input_dir, output_dir)

if __name__ == "__main__":
    main()
