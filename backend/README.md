# WebMind Backend

## Overview

This folder contains the FastAPI backend responsible for website crawling, content extraction, semantic indexing, vector search, and AI-powered question answering.

---

## Tech Stack

* Python
* FastAPI
* Uvicorn
* BeautifulSoup
* Requests
* Playwright
* FAISS
* Sentence Transformers
* Groq API

---

## Backend Modules

### Crawler

Recursively crawls internal website pages.

### Extraction

Extracts clean readable content from webpages.

### Chunking

Splits extracted content into overlapping chunks.

### Embeddings

Converts chunks into vector embeddings.

### Vector Store

Stores embeddings using FAISS.

### Retriever

Performs semantic similarity search.

### LLM Service

Generates grounded answers using retrieved context.

---

## Environment Setup

Before running the backend, you must configure your environment variables:

1. Copy the example environment file to create your own local `.env` file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and add your own real API keys (e.g., Groq, Gemini).
3. **Important:** Never commit `backend/.env` to source control. It is already added to `.gitignore` to prevent leaking secrets.

---

## Run

```bash
python -m venv venv

# Windows
venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend URL

```
http://127.0.0.1:8000
```

Swagger Documentation

```
http://127.0.0.1:8000/docs
```
