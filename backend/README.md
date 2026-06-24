# WebMind – RAG Powered Website Chatbot (Backend)

Welcome to the backend project for WebMind, a Retrieval-Augmented Generation (RAG) powered website chatbot. This service provides the FastAPI backend and Gemini API connection.

## Setup Instructions (Windows)

Follow these steps to set up and run the backend server on Windows:

### 1. Configure Environment Variables
1. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/).
2. Copy the template environment file `.env.example` to `.env` inside the `backend` folder:
   ```cmd
   copy .env.example .env
   ```
3. Open `.env` and paste your Gemini API key:
   ```env
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### 2. Set Up Virtual Environment and Dependencies
1. Open your terminal in the `backend` directory.
2. Create a Python virtual environment:
   ```cmd
   python -m venv venv
   ```
3. Activate the virtual environment:
   ```cmd
   venv\Scripts\activate
   ```
4. Install the required dependencies:
   ```cmd
   pip install -r requirements.txt
   ```
5. Install Playwright browser dependencies:
   ```cmd
   pip install playwright
   playwright install chromium
   ```

### 3. Run Gemini Self-Tests

To verify that your Gemini API key and connection work correctly, run the self-test script:
```cmd
python app/gemini_client.py
```

### 4. Run URL Validator Self-Tests
To run the direct validation test script:
```cmd
python app/ingestion/url_validator.py
```

### 5. Run Content Type Detector Self-Tests
To execute the direct content type resolution tests:
```cmd
python app/ingestion/content_type_detector.py
```

### 6. Run HTML Ingestor Self-Tests
To execute the static page download, tag stripping, text cleanup, and hyperlink resolution tests:
```cmd
python app/ingestion/html_ingestor.py
```

### 7. Run Same-Domain Crawler Self-Tests
To execute the multi-page domain-restricted crawler tests:
```cmd
python app/crawler/generic_crawler.py
```

### 8. Run PDF Ingestor Self-Tests
To run the PDF downloader and text extractor tests:
```cmd
python app/ingestion/pdf_ingestor.py
```

### 9. Run JSON Ingestor Self-Tests
To run the JSON formatter tests:
```cmd
python app/ingestion/json_ingestor.py
```

### 10. Run Ingestion Router Self-Tests
To run the unified routing checks resolving both PDF and JSON links:
```cmd
python app/ingestion/ingestion_router.py
```

### 11. Run Playwright Ingestor Self-Tests
To execute the dynamic page rendering tests extracting content from JS-only websites:
```cmd
python app/ingestion/dynamic_page_ingestor.py
```

### 12. Run Content Extraction and Cleaning Router Self-Tests
To execute the unified content cleaner, table, metadata, JSON-LD, and structured product data extractors self-test:
```cmd
python -m app.extractors.extraction_router
```

### 13. Run Text Chunker Self-Tests
To execute the sliding-window text splitter and sentence boundaries verification tests:
```cmd
python -m app.rag.chunker
```

### 14. Run Gemini Embeddings Self-Tests
To generate vector embeddings for chunks and run dimension verification checks:
```cmd
python -m app.rag.embeddings
```

### 15. Run FAISS Vector Store Self-Tests
To verify L2 vector normalization, index building, disk save/loads, and index clearing:
```cmd
pip install faiss-cpu numpy
python -m app.rag.vector_store
```

### 16. Run Semantic Search Retriever Self-Tests
To execute semantic retrieval search checks querying user questions against FAISS and formatting output contexts:
```cmd
python -m app.rag.retriever
```

### 17. Run RAG Answer Generator Self-Tests
To execute context-grounded answer generation queries using Gemini and check strict fallback controls:
```cmd
python -m app.rag.answer_generator
```

### 18. Run Full Website Ingestion Service Self-Tests
To execute the crawl, extract, chunk, embed, and FAISS indexing orchestration:
```cmd
python -m app.services.ingest_service
```

### 19. Run Chat Service Self-Tests
To execute retrieval and answer generation queries for indexed websites:
```cmd
python -m app.services.chat_service
```

### 20. Run the FastAPI Development Server
Start the Uvicorn development server:
```cmd
uvicorn app.main:app --reload
```

---

## Static vs Dynamic Page Ingestion Fallback

To maximize crawling performance and lower latency, WebMind splits HTML ingestion:
- **Static Ingestion**: Pages are initially requested using `requests` and parsed with `BeautifulSoup`. This keeps resource consumption and latency extremely low.
- **Dynamic Browser Fallback**: If the statically extracted text length is under `DYNAMIC_PAGE_TEXT_THRESHOLD` (default 300 characters), the backend assumes the page is a dynamic Client-Side Rendered (CSR) app relying on JavaScript. It triggers a headless Playwright Chromium instance to render the page fully before performing content extraction.

---

## Text Chunking & Context Preservation in RAG

To build an accurate Retrieval-Augmented Generation (RAG) system, extracted webpage and document texts must be split before being embedded:
1. **Text Chunking**: Large pages exceed context windows and diluting semantic meanings. Splitting text into smaller pieces (approx. 1000 characters) ensures precise similarity matching with search queries.
2. **Contextual Overlap**: When splitting text, there is a risk of losing information that sits on the boundary. We add a sliding window overlap (default 150 characters) so that consecutive chunks share boundary words/sentences, maintaining continuous semantic flow.
3. **Punctuation Boundaries**: We scan backwards inside the search window to split near newlines or sentence-ending punctuation (`.`, `!`, `?`, or space) rather than cutting words in the middle.
4. **Metadata Preservation**: Every chunk retains its source URL, page title, section header (where applicable), and PDF page numbers. This allows the LLM to generate precise citations linking answers back to the original source.

---

## Text Chunk Embedding & Vector Storage

Once text is chunked, WebMind translates it into vectors and indexes them:
1. **Vector Embedding**: Each text chunk is sent to the Gemini API (`gemini-embedding-001`). Gemini converts natural language text into a high-dimensional mathematical vector (typically 768 dimensions, or 3072 depending on model features). In this vector space, texts with similar semantic meanings are placed close together.
2. **Task Configuration**: Website chunks are embedded using the `RETRIEVAL_DOCUMENT` task type, preparing them for semantic search retrieval.
3. **Local FAISS Storage**: WebMind uses **FAISS** (Facebook AI Similarity Search) to index and query vector spaces locally:
   - **NumPy Normalization**: Chunks are cast as `float32` arrays and L2-normalized using NumPy prior to indexing. This allows FAISS's `IndexFlatIP` (Inner Product index) to perform exact Cosine Similarity calculations.
   - **Isolation by Website**: Each website gets its own dedicated folder under `data/indexes/<website_id>/` storing the FAISS index map (`index.faiss`), structural parameters (`store_info.json`), and content metadata (`metadata.json`).
   - **Metadata Mapping**: Since FAISS indexes only store anonymous coordinate lists, positions in the FAISS index map 1-to-1 to entries in `metadata.json` (holding original chunk text, headings, and URLs) for reference during retrieval.

## Semantic Query Retrieval & Context Formatting

Once the local vector database is built, WebMind utilizes semantic retrieval during query time:
1. **Query Embedding**: User questions are converted to vectors using Gemini (`gemini-embedding-001`). Crucially, questions are embedded using the `RETRIEVAL_QUERY` task type configuration, aligning them with the previously stored `RETRIEVAL_DOCUMENT` vectors.
2. **Normalized Cosine Match**: The query vector is L2-normalized using NumPy and queried against the FAISS index to extract the `top_k` closest match positions and similarity scores.
3. **Chunk Mapping**: Numerical positions returned by FAISS are mapped back to actual metadata records inside `metadata.json` (resolving source URLs, titles, headings, and page numbers).
4. **Context Construction**: Selected chunks are formatted into a clean, text-concatenated block:
   ```text
   [Source 1]
   Title: ...
   URL: ...
   Heading: ...
   Content:
   ...
   ```
   This block acts as the grounding context, which in the next step will be sent along with the user's question to the Gemini chat model for final grounded answer generation.

## Grounded Answer Generation & Citation Tracking

At the end of the RAG pipeline, WebMind generates strict, context-bound responses:
1. **Context Grounding**: The retriever supplies the formatted context matching the user's query.
2. **Model Selection**: Answer generation is powered by `gemini-2.5-flash` by default, providing fast, high-quality reasoning.
3. **Strict System Instructions**: Gemini receives explicit instructions preventing external knowledge usage, hallucination, or mentioning its AI identity. If the answer is not present in the context, it must return exactly `"I could not find this information in the indexed website."`.
4. **Decoupled Citations**: Source mapping properties (URL, Title, and Heading) are extracted, deduped (up to 5 maximum), and returned separately in the API response payload, keeping sources transparent without cluttering the generated answer body.

---

## Website Indexing Limits

WebMind supports adjustable crawling depth for different types of websites:

| Limit | Best for | Notes |
| 1–10 | Quick tests | Fast |
| 25 | Most websites | Recommended |
| 50 | Documentation/blogs | More coverage |
| 100 | Large sites | Slower and uses more API quota |

---

## Universal Question-Aware Crawl Relevance Scoring (Step 17)

To optimize crawling sequence and ensure that the most important context pages are indexed first under a limited `max_pages` budget, WebMind implements a **Universal Question-Aware Crawl Relevance Scoring** system:

1. **Question Intent Matching**:
   - Analyzes normalized, tokenized words from the user's `initial_question` (filtering out standard English stop words).
   - Scores matches in discovered links: Path & Query matches (+4.0), Anchor Text matches (+3.0), Title & Aria-Label attributes (+2.0), and Source Page Title (+1.0).
   - Grants co-occurrence bonuses (+5.0) if multiple keywords appear in the same path/anchor.

2. **Heuristic Boosting & Penalties**:
   - **Intent Boosts (+8.0)**: Automatically detects user intents like *download/install*, *documentation/tutorials*, *pricing*, *products/shopping*, *support/help*, *login/accounts*, or *about/company* and boosts matching links.
   - **Low-Value Penalties**: Suppresses irrelevant URLs by penalizing privacy policies (-12.0), generic login/register (-8.0), social media widgets (-10.0), share/feed links (-8.0), and foreign language paths (-5.0).
   - **Quality Check Bonuses**: Prefers short URLs (+2.0), child links closer to root (+1.0), and penalizes query overload (-2.0) or tracking parameters (-3.0).
   - **Fallback Boosts (+5.0)**: When no question is provided, general pages matching reference docs, tutorials, FAQs, products, or blogs receive a default boost.

3. **Global Queue Prioritization**:
   - Upon discovering links on a page, they are ranked, and their relevance details (`relevance_score`, `relevance_reason`, `matched_terms`) are saved globally.
   - Discovered same-domain links are pushed to the queue.
   - The entire `CrawlQueue` is sorted globally descending by score (with shortest URL length ascending as a tie-breaker) on every iteration.
   - Each crawled page stores `crawl_relevance_score`, `crawl_reason`, and `matched_terms` in its metadata registry.

---
## Testing URLs

Once the FastAPI server is running, you can access the following URLs in your web browser:

- **Root Status Endpoints**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) - Verifies the backend server is running.
- **Health Check Endpoint**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) - Evaluates backend health and checks Gemini API connection.
- **Interactive Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) - Test the endpoints directly from the interactive UI.

---

## API References

### 1. POST /validate-url
Validate and normalize a crawling URL safely against SSRF.

- **Request Example**:
  ```json
  {
    "url": "python.org"
  }
  ```
- **Response Example**:
  ```json
  {
    "valid": true,
    "normalized_url": "https://python.org",
    "message": "URL is valid"
  }
  ```

### 2. POST /detect-content-type
Validate a target URL first, then determine its content type (HTML, PDF, JSON, Plain Text) safely without downloading full payloads.

- **Request Example**:
  ```json
  {
    "url": "https://www.python.org"
  }
  ```
- **Response Example**:
  ```json
  {
    "success": true,
    "final_url": "https://www.python.org/",
    "status_code": 200,
    "content_type": "html",
    "raw_content_type": "text/html; charset=utf-8",
    "message": "Content type detected successfully"
  }
  ```

### 3. POST /ingest-html
Validate a target URL, confirm it is of HTML format, then scrape and structure page content.

- **Request Example**:
  ```json
  {
    "url": "https://www.python.org"
  }
  ```
- **Response Example**:
  ```json
  {
    "success": true,
    "final_url": "https://www.python.org/",
    "title": "Welcome to Python.org",
    "description": "The official home of the Python Programming Language",
    "headings": [
      "Welcome to Python.org",
      "Search",
      "Downloads"
    ],
    "text": "Python is a programming language that lets you work quickly...",
    "links": [
      "https://www.python.org/",
      "https://www.python.org/psf-landing/"
    ],
    "text_length": 6245,
    "message": "HTML content extracted successfully"
  }
  ```

### 4. POST /crawl
Validate a starting URL, extract its base domain, and perform a recursive same-domain crawl up to a maximum page limit.

- **Request Example**:
  ```json
  {
    "url": "https://www.python.org",
    "max_pages": 3
  }
  ```
- **Response Example**:
  ```json
  {
    "success": true,
    "start_url": "https://www.python.org",
    "pages_crawled": 3,
    "pages": [
      {
        "url": "https://www.python.org",
        "title": "Welcome to Python.org",
        "description": "The official home of the Python Programming Language",
        "headings": ["Welcome to Python.org", "Search"],
        "text": "Python is a programming language...",
        "links": ["https://www.python.org/downloads/"],
        "text_length": 4595
      }
    ],
    "visited_urls": [
      "https://www.python.org",
      "https://www.python.org/downloads/"
    ],
    "failed_urls": [],
    "message": "Website crawl completed successfully. Crawled 3 page(s)."
  }
  ```

### 5. POST /ingest-url
Validate a target URL, detect its content type, and ingest HTML, PDF, or JSON payloads into a unified format.

- **Request Example**:
  ```json
  {
    "url": "https://api.github.com"
  }
  ```
- **Response Example**:
  ```json
  {
    "success": true,
    "final_url": "https://api.github.com/",
    "content_type": "json",
    "text": "{\n  \"current_user_url\": \"https://api.github.com/user\",\n  ... \n}",
    "data": {
      "current_user_url": "https://api.github.com/user"
    },
    "text_length": 2045,
    "message": "JSON content extracted successfully"
  }
  ```

### 6. POST /ingest
Orchestrates crawler, extractor, chunker, embeddings, and FAISS vector storage into a single pipeline. The returned `website_id` is required for querying questions against this indexed target later in the chat step.

- **Request Example**:
  ```json
  {
    "url": "https://www.python.org",
    "max_pages": 2,
    "initial_question": ""
  }
  ```
- **Response Example**:
  ```json
  {
    "success": true,
    "website_id": "python_org_a1b2c3d4",
    "source_url": "https://www.python.org/",
    "content_type": "html",
    "pages_crawled": 2,
    "documents_processed": 2,
    "chunks_created": 15,
    "chunks_embedded": 15,
    "chunks_failed": 0,
    "vector_store_stats": {
      "vector_count": 15,
      "dimension": 768
    },
    "message": "Website crawled and indexed successfully"
  }
  ```

### 7. POST /chat
Submits user questions and retrieves context-grounded RAG answers matching the requested `website_id`.

- **Request Example**:
  ```json
  {
    "website_id": "python_org_f830ae59",
    "question": "How can I download Python?",
    "top_k": 5
  }
  ```
- **Response Example**:
  ```json
  {
    "success": true,
    "website_id": "python_org_f830ae59",
    "question": "How can I download Python?",
    "answer": "You can download Python from the official downloads page. Pre-compiled binary installers are available for Windows, macOS, and Linux.",
    "sources": [
      {
        "url": "https://www.python.org/downloads",
        "title": "Welcome to Python.org",
        "heading": "Downloads"
      }
    ],
    "retrieved_chunks_count": 5,
    "used_context_fallback": false,
    "message": "Answer generated successfully"
  }
  ```





