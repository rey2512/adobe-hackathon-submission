import os
import json
import time
import statistics
from pathlib import Path
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer, util

# --- OPTIMIZATION: Set a limit on pages to process for large documents ---
MAX_PAGES_TO_PROCESS = 75

def extract_text_from_pdf(pdf_path):
    """
    Extracts structured sections from a PDF document by identifying headings
    and grouping the text content under them. Limits processing to MAX_PAGES_TO_PROCESS.
    """
    doc = fitz.open(pdf_path)
    if len(doc) == 0:
        return []

    page_count_to_process = min(len(doc), MAX_PAGES_TO_PROCESS)
    if len(doc) > MAX_PAGES_TO_PROCESS:
        print(f" - INFO: Document has {len(doc)} pages. Processing the first {MAX_PAGES_TO_PROCESS} pages to stay within time limits.")

    # --- Pass 1: Identify potential headings with the most advanced logic ---
    headings = []
    all_font_sizes = []
    
    for page_num in range(page_count_to_process):
        page = doc[page_num]
        blocks = page.get_text("dict").get("blocks", [])
        for b in blocks:
            if "lines" in b:
                for l in b["lines"]:
                    for s in l["spans"]:
                        if s["text"].strip():
                            all_font_sizes.append(s["size"])

    if not all_font_sizes:
        return []

    median_size = statistics.median(all_font_sizes)
    
    allowed_single_words = {"content", "contents", "notice", "introduction", "summary", "conclusion", "appendix", "glossary", "financials", "operations", "value"}

    for page_num in range(page_count_to_process):
        page = doc[page_num]
        blocks = page.get_text("dict").get("blocks", [])
        for b in blocks:
            if "lines" in b:
                for l in b["lines"]:
                    if l.get("spans"):
                        span = l["spans"][0]
                        font_size = span["size"]
                        text = " ".join(s["text"] for s in l["spans"]).strip()

                        is_large_enough = font_size > median_size * 1.20
                        is_not_just_number = not text.replace('.', '', 1).replace('%', '').replace('+', '').replace('k', '').isdigit()
                        is_long_enough = len(text) > 3 and len(text) < 150
                        is_not_a_sentence = not text.endswith('.') and not text.endswith(',')
                        is_title_case = text.istitle() or text.isupper()
                        word_count = len(text.split())
                        is_concise = word_count < 10
                        is_valid_single_word = word_count > 1 or (word_count == 1 and text.lower() in allowed_single_words)

                        if is_large_enough and is_not_just_number and is_long_enough and is_not_a_sentence and is_title_case and is_concise and is_valid_single_word:
                            headings.append({
                                "text": text,
                                "page": page_num,
                                "y": span["bbox"][1]
                            })

    unique_headings = []
    seen_texts = set()
    for h in sorted(headings, key=lambda x: (x["page"], x["y"])):
        if h["text"].lower() not in seen_texts:
            unique_headings.append(h)
            seen_texts.add(h["text"].lower())
    
    sorted_headings = unique_headings

    sections = []
    if not sorted_headings:
        print(f" - WARNING: No headings found in {pdf_path.name}. Falling back to simple block extraction.")
        for page_num in range(page_count_to_process):
            page = doc[page_num]
            blocks = page.get_text("blocks")
            for i, block in enumerate(blocks):
                text = block[4].strip().replace('\n', ' ')
                if len(text) > 150:
                    sections.append({
                        "doc_name": pdf_path.name,
                        "page_number": page_num + 1,
                        "section_title": f"Page {page_num + 1}, Section {i+1}",
                        "full_text": text
                    })
        return sections

    for i, heading in enumerate(sorted_headings):
        start_page = heading["page"]
        start_y = heading["y"]

        end_page = page_count_to_process
        end_y = float('inf')
        if i + 1 < len(sorted_headings):
            next_heading = sorted_headings[i+1]
            end_page = next_heading["page"]
            end_y = next_heading["y"]

        content = ""
        loop_end = min(end_page + 1, page_count_to_process)
        for page_num in range(start_page, loop_end):
            page_rect = doc[page_num].rect
            clip_rect = page_rect
            if page_num == start_page and page_num == end_page:
                clip_rect = fitz.Rect(0, start_y, page_rect.width, end_y)
            elif page_num == start_page:
                clip_rect = fitz.Rect(0, start_y, page_rect.width, page_rect.height)
            elif page_num == end_page:
                clip_rect = fitz.Rect(0, 0, page_rect.width, end_y)
            
            content += doc[page_num].get_text("text", clip=clip_rect)

        if content.strip():
            sections.append({
                "doc_name": pdf_path.name,
                "page_number": start_page + 1,
                "section_title": heading["text"],
                "full_text": content.strip().replace('\n', ' ')
            })

    doc.close()
    return sections

def run_analysis():
    """Main function to run the persona-driven analysis."""
    total_start_time = time.time()
    input_dir = Path('/app/input')
    output_dir = Path('/app/output')
    output_dir.mkdir(exist_ok=True)

    print("Step 1: Loading model...")
    t0 = time.time()
    model_path = 'models/all-MiniLM-L6-v2'
    model = SentenceTransformer(model_path)
    print(f"   > Model loaded in {time.time() - t0:.2f}s")

    print("Step 2: Loading persona...")
    with open(input_dir / 'persona.json', 'r', encoding='utf-8') as f:
        persona_data = json.load(f)
    persona = persona_data['persona']
    job_to_be_done = persona_data['job_to_be_done']

    print("Step 3: Processing all PDF documents...")
    t0 = time.time()
    all_sections = []
    
    # --- FIX: Use a more robust method to find all PDF files ---
    try:
        pdf_files = [input_dir / f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
        print(f"   > DEBUG: Found {len(pdf_files)} PDF files: {[p.name for p in pdf_files]}")
    except Exception as e:
        print(f"   > ERROR: Could not list files in {input_dir}. Reason: {e}")
        pdf_files = []

    if not pdf_files:
        print("   > WARNING: No PDF files found to process.")

    for pdf_file in pdf_files:
        print(f"- Extracting sections from {pdf_file.name}")
        all_sections.extend(extract_text_from_pdf(pdf_file))
    print(f"   > Extracted {len(all_sections)} total sections in {time.time() - t0:.2f}s")

    print("Step 4: Ranking sections...")
    t0 = time.time()
    query = f"User is a {persona}. Their goal is to: {job_to_be_done}"
    query_embedding = model.encode(query, convert_to_tensor=True)

    if all_sections:
        section_texts = [section['full_text'] for section in all_sections]
        section_embeddings = model.encode(section_texts, convert_to_tensor=True, batch_size=32)
        
        cosine_scores = util.cos_sim(query_embedding, section_embeddings)
        
        for i, section in enumerate(all_sections):
            section['relevance_score'] = cosine_scores[0][i].item()
    print(f"   > Ranking completed in {time.time() - t0:.2f}s")

    ranked_sections = sorted(all_sections, key=lambda x: x.get('relevance_score', -1), reverse=True)

    print("Step 5: Generating final output file...")
    final_output = {
        "metadata": {
            "input_documents": [p.name for p in pdf_files],
            "persona": persona,
            "job_to_be_done": job_to_be_done,
            "processing_timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        },
        "extracted_section": [],
        "sub-section_analysis": []
    }

    for i, section in enumerate(ranked_sections[:10]):
        final_output["extracted_section"].append({
            "document": section["doc_name"],
            "page_number": section["page_number"],
            "section_title": section["section_title"],
            "importance_rank": i + 1
        })
        final_output["sub-section_analysis"].append({
            "document": section["doc_name"],
            "refined_text": section["full_text"][:500] + "...",
            "page_number": section["page_number"]
        })

    output_path = output_dir / 'output.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print(f"\nSuccess! Total analysis time: {time.time() - total_start_time:.2f}s")
    print(f"Output saved to {output_path}")

if __name__ == '__main__':
    run_analysis()
