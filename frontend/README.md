# WebMind – RAG Powered Website Chatbot Frontend

Welcome to the premium frontend application for **WebMind**. This project is built using React, Vite, TypeScript, and Tailwind CSS. It communicates with a Python-based FAISS and Gemini RAG backend.

## Tech Stack Overview

- **Core Framework**: React 18 & TypeScript
- **Build Tool**: Vite (for ultra-fast hot module reloading)
- **Styling**: Tailwind CSS (for modern UI utility classes)
- **Icons**: Lucide React icons
- **State Management**: React Hooks with custom persistence layer via `localStorage`
- **Design System**: Sleek, glassmorphism dark-theme with purple and blue gradients

---

## Getting Started

### Prerequisites

Make sure you have [Node.js](https://nodejs.org) installed on your system.

### Installation & Launch

1. **Navigate to the frontend folder**:
   ```powershell
   cd frontend
   ```

2. **Install project dependencies**:
   ```bash
   npm install
   npm install react-router-dom
   ```

3. **Start the Vite development server**:
   ```powershell
   npm run dev
   ```

4. **Access the application**:
   Open [http://localhost:5173](http://localhost:5173) in your web browser.

---

## Running the Backend

The frontend connects to the backend API at `http://127.0.0.1:8000` (configured in `.env`). The backend must run concurrently to process URL indexing and RAG queries:

```powershell
# Open a separate terminal / command prompt
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

---

## Configuration

Environment variables can be customized in the `.env` file:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```
