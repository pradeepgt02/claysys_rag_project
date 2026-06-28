---
title: WebMind
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

﻿# WebMind - RAG Powered Website Chatbot

## 🚀 Overview

WebMind is an AI-powered **Retrieval-Augmented Generation (RAG)** chatbot that transforms any website into an intelligent, searchable knowledge base.

Users simply provide a website URL, and WebMind automatically crawls the website, extracts meaningful content, creates semantic embeddings, stores them in a FAISS vector database, and answers user questions using only the indexed website content.

Unlike traditional AI chatbots, WebMind provides **source-grounded answers**, reducing hallucinations by retrieving relevant website content before generating responses.

---

# ✨ Features

* 🌐 Index any public website
* 🔍 Intelligent recursive website crawling
* 📄 Automatic content extraction and cleaning
* ✂️ Smart text chunking with overlap
* 🧠 Semantic search using FAISS vector database
* 💬 AI-powered question answering
* 📚 Source citations for every response
* 🗂️ Multiple website knowledge bases
* 📝 Chat history management
* 🛡️ Hallucination reduction using retrieval validation
* ⚡ Fast semantic retrieval
* 🎯 Responsive and modern UI

---

# 🏗️ System Architecture

```text
                  User
                    │
                    ▼
          React Frontend (TypeScript)
                    │
                    ▼
           FastAPI Backend (Python)
                    │
        ┌───────────┴────────────┐
        │                        │
        ▼                        ▼
 Website Crawler         Chat Request
        │                        │
        ▼                        ▼
 Content Extraction     Question Embedding
        │                        │
        ▼                        ▼
 Text Chunking         FAISS Similarity Search
        │                        │
        ▼                        ▼
 Embedding Creation    Relevant Chunks
        │                        │
        └──────────────┬─────────┘
                       ▼
               Groq LLM Generation
                       ▼
            Source Grounded Answer
                       ▼
                React Chat Interface
```

---

# 🛠 Tech Stack

## Frontend

* React
* TypeScript
* Vite
* Tailwind CSS
* Lucide React

## Backend

* Python
* FastAPI
* Uvicorn
* Pydantic

## AI / RAG

* FAISS Vector Database
* Sentence Transformers
* Groq API

## Crawling

* Requests
* BeautifulSoup
* Playwright (Dynamic Websites)

---

# 📁 Project Structure

```
WebMind/
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   └── services/
│
├── backend/
│   ├── app/
│   │   ├── crawler/
│   │   ├── extraction/
│   │   ├── ingestion/
│   │   ├── rag/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── data/
│   │   └── indexes/
│   │
│   ├── requirements.txt
│   └── .env.example
│
└── README.md
```

---

# ⚙️ Installation

## Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/WebMind.git
cd WebMind
```

---

## Backend Setup

```bash
cd backend

python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

Create a `.env` file inside the backend folder:

```env
GROQ_API_KEY=YOUR_API_KEY
```

Start the backend:

```bash
uvicorn app.main:app --reload
```

---

## Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

---

# 📌 How It Works

### Step 1

User enters a website URL.

### Step 2

The crawler recursively visits relevant pages within the same domain.

### Step 3

Meaningful content is extracted from each page.

### Step 4

Content is divided into smaller chunks.

### Step 5

Chunks are converted into embeddings.

### Step 6

Embeddings are stored in a FAISS vector database.

### Step 7

When a user asks a question:

* Question embedding is generated.
* Relevant chunks are retrieved from FAISS.
* Retrieved context is sent to the LLM.
* A grounded answer with references is returned.

---

# 🎯 Hallucination Prevention

To improve answer reliability, WebMind:

* Retrieves only relevant website chunks.
* Uses similarity score validation.
* Uses keyword-overlap validation.
* Generates answers only from retrieved website content.
* Returns "Information not found" when sufficient evidence is unavailable.

---

# 📸 Screenshots

Add screenshots of:

* Home Page
* Website Indexing
* Chat Interface
* Indexed Pages
* Source References
* Chat History

---

# 🚀 Future Improvements

* Background website indexing
* Incremental re-indexing
* Sitemap.xml support
* Robots.txt compliance
* Authentication
* User-specific knowledge bases
* Cloud deployment
* Redis caching
* Hybrid keyword + vector search
* Multi-language support

---

# 👨‍💻 Author

**Pradeep Kumar M**

B.Tech – Artificial Intelligence and Machine Learning

Sri Shakthi Institute of Engineering and Technology

GitHub: https://github.com/pradeepgt02

LinkedIn: https://www.linkedin.com/in/pradeepkumar-m-21685a335/

---

# 📄 License

This project is intended for educational and hackathon purposes.
