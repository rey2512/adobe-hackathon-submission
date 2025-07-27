# 📘 Persona-Driven Document Intelligence System

An intelligent, offline-ready PDF analysis tool that uses **semantic search** to extract and rank relevant sections from documents, tailored to a user's **role (persona)** and **goal (job-to-be-done)** — perfect for research and deep document understanding.

---

## What It Does

This system acts as an intelligent research assistant. It doesn’t just search for keywords — it understands context.

By combining **structural document analysis** with **sentence-transformer embeddings**, it extracts meaningful sections and ranks them using **cosine similarity** against your goal description (e.g., "analyze revenue trends").

All processing is done **offline** and with **CPU only**, making it hackathon-compliant and privacy-preserving.

---

## How to Use

### Step 1: Prepare Your Inputs

1. Create a folder named `input/` in the root of the project.
2. Add your PDF files to `input/`.
3. Add a `persona.json` file inside `input/` :



### Step 2: Build the Docker Image

Open terminal in the project root directory and run:

```bash
docker build -t adobe-hackathon-solution .
```

---

### Step 3: Run the System

#### For Windows (PowerShell):

```powershell
docker run --rm -v "${PWD}\input:/app/input" -v "${PWD}\output:/app/output" --network none adobe-hackathon-solution
```

#### For macOS/Linux:

```bash
docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" --network none adobe-hackathon-solution
```

✅ Output will be saved in the `output/` folder as `output.json`.

---

## 📂 Project Structure


adobe_round1b/
├── main.py                 # Main application logic
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container setup
├── approach_explanation.md # Technical methodology
├── README.md               # This file
├── input/                  # Input files (PDFs + persona.json)
├── output/                 # Output file (output.json)
└── models/                 # Pre-downloaded 

---

## ⚙️ How It Works Internally

### 1. Section Extraction

* Uses `PyMuPDF (fitz)` to extract text blocks from PDFs.
* Detects headings using font size and style.
* Groups content under each heading to form logical sections.

### 2. Semantic Embedding

* Uses the `all-MiniLM-L6-v2` model (from SentenceTransformers) to embed:

  * The **user query** (persona + job).
  * Each **document section**.

### 3. Similarity Calculation

* Uses **cosine similarity** to measure how closely each section matches the user's intent.

### 4. Ranking & Output

* Top 10 most relevant sections are ranked and saved in a structured JSON file.

---

## 🧾 Output Format (`output/output.json`)

```json
{
  "metadata": {
    "input_documents": [
      "doc1.pdf",
      "doc2.pdf"
    ],
    "persona": "Investment Analyst",
    "job_to_be_done": "Analyze revenue trends over the last 4 quarters...",
    "processing_timestamp": "2025-07-27 10:00:00"
  },
  "extracted_section": [
    {
      "document": "doc1.pdf",
      "page_number": 5,
      "section_title": "Q4 Financial Highlights",
      "importance_rank": 1
    }
  ],
  "sub-section_analysis": [
    {
      "document": "doc1.pdf",
      "refined_text": "The fourth quarter saw a significant increase in revenue...",
      "page_number": 5
    }
  ]
}
```

---

## 📌 Notes

**must** download the sentence-transformer model (`all-MiniLM-L6-v2`) into the `models/` folder before building the Docker image.
* No internet or GPU is used — fully offline and CPU-only.

