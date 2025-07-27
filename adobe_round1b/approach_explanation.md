**Approach Explanation: Persona-Driven Document Intelligence**


Introduction

The goal of this project was to build an intelligent document analyst capable of navigating a collection of PDF documents to find sections most relevant to a specific user's role and task. We moved beyond simple keyword matching to develop a semantic system that understands the user's context, as defined by their Persona and Job-to-be-Done, and retrieves conceptually related content.

Methodology

Our solution follows a three-stage pipeline: intelligent section extraction, persona-driven embedding and ranking, and final output generation.

1. Intelligent Section Extraction
To ensure our analysis is based on meaningful, complete sections, we first parse each PDF to understand its structure. Using the PyMuPDF (fitz) library, we perform a two-pass analysis similar to our Round 1A solution. We first identify text that serves as a structural heading based on font size and style. We then extract the full text content that falls between one heading and the next, creating complete, logical sections. For documents without clear headings, the system gracefully falls back to segmenting the content into coherent text blocks.

2. Persona-Driven Embedding and Ranking
This is the core of our intelligent system. We use the sentence-transformers library with the all-MiniLM-L6-v2 model, which provides an excellent balance of performance and accuracy on CPU-only hardware.

Query Formulation: We form a rich, descriptive query by combining the user's Persona and Job-to-be-Done. For example, "User is a PhD Researcher in Computational Biology. Their goal is to: Prepare a comprehensive literature review..."

Embedding Generation: We convert this persona-driven query into a high-dimensional vector (embedding). We then do the same for every document section extracted in the previous stage. These embeddings capture the semantic meaning of the text.

Similarity Ranking: We use Cosine Similarity to calculate the contextual relevance between the persona's query embedding and each section's embedding. This gives us a precise score for how well each section matches the user's specific need. The sections are then ranked from highest to lowest score.

3. Output Generation

The final ranked list is formatted into the required JSON structure. The importance_rank is determined by the sorted relevance scores. For the sub-section_analysis, we provide a snippet of the top-ranked sections' text to give the user a quick preview of the relevant content.

Tools and Libraries

PyMuPDF (fitz): For robust and accurate text extraction from PDF documents.

sentence-transformers: To access the state-of-the-art all-MiniLM-L6-v2 model for generating powerful semantic text embeddings.

PyTorch: The underlying framework that powers the sentence-transformer models.

This approach creates a powerful and context-aware system that acts as a true research assistant, connecting users to the information that matters most to them.