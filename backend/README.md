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
