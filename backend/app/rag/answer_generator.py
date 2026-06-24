import sys
from pathlib import Path

# Add parent directory of this file to sys.path to support running this script directly
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from app.gemini_client import config, generate_chat_response
from app.rag.retriever import format_retrieved_context

def build_rag_prompt(question: str, context: str) -> str:
    """Builds a formatted prompt combining the question and context."""
    return f"Website Context:\n{context}\n\nUser Question:\n{question}\n\nAnswer:"

def build_safe_context_fallback(question: str, top_chunk: dict) -> str | None:
    import re
    
    text = top_chunk.get("text", "")
    if not text:
        return None
        
    question_lower = question.lower()
    
    # 1. Clean navigation lines
    nav_words = {"home", "next", "docs", "jobs", "latest news", "more"}
    lines = text.split('\n')
    valid_lines = []
    for line in lines:
        line_clean = line.strip()
        # skip short lines
        if len(line_clean.split()) < 3:
            continue
        # skip nav
        if line_clean.lower() in nav_words:
            continue
        # skip dates (very rough heuristic: looks like date)
        if re.match(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}$', line_clean):
            continue
        # skip simple URLs
        if re.match(r'^https?://[^\s]+$', line_clean):
            continue
        valid_lines.append(line_clean)
        
    cleaned_text = " ".join(valid_lines)
    
    # 2. Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', cleaned_text)
    
    # 3. Keyword matching
    # Determine intent
    is_download = any(w in question_lower for w in ["download", "install"])
    is_docs = any(w in question_lower for w in ["document", "tutorial", "guide", "learn", "doc"])
    is_pricing = any(w in question_lower for w in ["price", "pricing", "cost", "plan"])
    
    download_words = {"download", "installer", "install", "installation", "get python", "source code"}
    docs_words = {"documentation", "tutorial", "guide", "learn", "docs"}
    pricing_words = {"price", "pricing", "cost", "plan"}
    
    selected_sentences = []
    
    for sentence in sentences:
        s_lower = sentence.lower()
        valid = False
        
        if is_download:
            valid = any(w in s_lower for w in download_words)
        elif is_docs:
            valid = any(w in s_lower for w in docs_words)
        elif is_pricing:
            valid = any(w in s_lower for w in pricing_words)
        else:
            # General keyword overlap check
            STOP_WORDS = {"what", "is", "the", "of", "a", "an", "in", "to", "for", "on", "with", "how", "can", "i", "you", "we", "they", "he", "she", "it", "and", "or", "but", "about", "are", "do", "does", "did", "was", "were", "be", "been", "being", "have", "has", "had", "this", "that", "these", "those"}
            q_words = set(re.findall(r'\b\w+\b', question_lower)) - STOP_WORDS
            valid = any(w in s_lower for w in q_words)
            
        if valid:
            selected_sentences.append(sentence.strip())
            if len(selected_sentences) == 2:
                break
                
    if not selected_sentences:
        return None
        
    fallback = "Based on the indexed website: " + " ".join(selected_sentences)
    if len(fallback) > 350:
        fallback = fallback[:347] + "..."
        
    return fallback

def generate_rag_answer(
    question: str,
    retrieved_results: list[dict]
) -> dict:
    """
    Generates a RAG-grounded answer using the configured Gemini chat model.
    
    Flow:
    1. Validates that the question is not empty.
    2. Builds the context using format_retrieved_context.
    3. If the context is empty, returns the default fallback:
       "I could not find this information in the indexed website."
    4. Passes the strict context rules as a system_instruction.
    5. Calls the Gemini API using generate_chat_response.
    6. If Gemini fails (503, quota, network, etc.), uses context fallback
       if the retrieved context is relevant based on keyword overlap.
    """
    fallback_answer = "I could not find this information in the indexed website."

    # 1. Structure sources early so we have them for any early returns
    seen_urls = set()
    sources = []
    if retrieved_results:
        for res in retrieved_results:
            if not isinstance(res, dict):
                continue
            url = res.get("source_url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                sources.append({
                    "url": url,
                    "title": res.get("title", "") or "Untitled Document",
                    "heading": res.get("heading", "") or "N/A"
                })
                if len(sources) >= 5:
                    break

    # 2. Validate inputs
    if not question or question.strip() == "":
        return {
            "success": False,
            "question": "",
            "answer": fallback_answer,
            "sources": [],
            "context_chunks_used": 0,
            "message": "Question cannot be empty."
        }

    if not retrieved_results:
        return {
            "success": True,
            "question": question,
            "answer": fallback_answer,
            "sources": [],
            "context_chunks_used": 0,
            "message": "No retrieved results found. Fallback answer returned."
        }

    # 3. Format context
    context = format_retrieved_context(retrieved_results)
    if not context or context.strip() == "":
        return {
            "success": True,
            "question": question,
            "answer": fallback_answer,
            "sources": [],
            "context_chunks_used": 0,
            "message": "Retrieved context is empty. Fallback answer returned."
        }

    # 4. Build prompt and configure strict system instructions
    prompt = build_rag_prompt(question, context)
    
    system_instruction = (
        "You are WebMind, a website question-answering assistant.\n\n"
        "Rules:\n"
        "1. Answer ONLY using the provided website context.\n"
        "2. Do not use outside knowledge.\n"
        "3. Do not invent facts, steps, links, or details.\n"
        "4. If the answer is not clearly present in the context, respond exactly:\n"
        '"I could not find this information in the indexed website."\n'
        "5. Keep the answer concise, clear, and useful.\n"
        "6. Do not mention that you are an AI model.\n"
        "7. Do not include source URLs inside the answer because sources are returned separately."
    )

    # 5. Call Gemini API using generate_chat_response wrapper
    res = generate_chat_response(prompt, system_instruction=system_instruction)
    
    if res["status"] == "success":
        answer_text = res["response"]
        if not answer_text or answer_text.strip() == "":
            answer_text = fallback_answer

        # Grounding validation (Hallucination check)
        if answer_text != fallback_answer:
            import re
            # Extract capitalized words (e.g., Python, Windows) and numbers
            # Exclude words starting sentences. Simplistic heuristic.
            words = re.findall(r'\b[A-Z][a-z]+\b|\b\d+\b', answer_text)
            if words:
                context_lower = context.lower()
                matches = sum(1 for w in words if w.lower() in context_lower)
                # If less than 50% of the key nouns/numbers are in context, it's likely hallucinating
                if matches / len(words) < 0.5:
                    answer_text = fallback_answer

        return {
            "success": True,
            "question": question,
            "answer": answer_text.strip(),
            "sources": sources,
            "context_chunks_used": len(retrieved_results),
            "message": "Answer generated successfully"
        }
    else:
        # Gemini failed (quota, 503, network error, or general API failure)
        message = "Gemini unavailable and no safe relevant fallback found"
        fallback_msg = "I could not generate a verified answer right now because the AI service is temporarily unavailable. Please retry."
        
        if retrieved_results:
            top_chunk = retrieved_results[0]
            similarity_score = top_chunk.get("similarity_score", 1.0) # default to 1.0 if not provided
            MIN_RELEVANCE_SCORE = 0.40
            
            if similarity_score >= MIN_RELEVANCE_SCORE:
                safe_fallback = build_safe_context_fallback(question, top_chunk)
                if safe_fallback:
                    return {
                        "success": True,
                        "answer": safe_fallback,
                        "sources": sources[:1],
                        "context_chunks_used": len(retrieved_results),
                        "used_context_fallback": True,
                        "message": "Gemini temporarily unavailable — verified context fallback used"
                    }
                    
        return {
            "success": False,
            "question": question,
            "answer": fallback_msg,
            "sources": [],
            "context_chunks_used": len(retrieved_results),
            "used_context_fallback": False,
            "message": message
        }

if __name__ == "__main__":
    print("=" * 70)
    print("Running RAG Answer Generator self-tests...")
    print("=" * 70)

    # We will monkeypatch generate_chat_response to simulate failures for Tests A and B
    import app.rag.answer_generator as ag
    
    original_generate = ag.generate_chat_response
    
    def mock_gemini_failure(*args, **kwargs):
        return {"status": "error", "message": "Simulated failure"}
        
    def mock_gemini_success(*args, **kwargs):
        return {"status": "success", "response": "Python 3.15 is the latest version. It costs 500 dollars."} # Deliberate hallucination

    # Test A
    sample_chunk_A = {
        "chunk_id": "1",
        "text": "Home\nJobs\nLatest News\nPython source code and installers are available for download for all versions.\nNext",
        "source_url": "https://python.org",
        "title": "Python",
        "similarity_score": 0.85
    }
    
    q_A = "how to download python"
    print(f"\n[Test Case A] Question: '{q_A}'")
    ag.generate_chat_response = mock_gemini_failure
    ans_A = generate_rag_answer(q_A, [sample_chunk_A])
    print("Success:", ans_A["success"])
    print("Answer:", ans_A["answer"])
    print("Used Fallback:", ans_A.get("used_context_fallback"))
    assert ans_A["used_context_fallback"] == True
    assert "download" in ans_A["answer"].lower()
    assert "Jobs" not in ans_A["answer"]

    # Test B
    sample_chunk_B = {
        "chunk_id": "2",
        "text": "Latest News\nJobs\nDocs\nPython 3.15 beta",
        "source_url": "https://python.org",
        "title": "Python",
        "similarity_score": 0.85
    }
    print(f"\n[Test Case B] Question: '{q_A}' (Bad context)")
    ans_B = generate_rag_answer(q_A, [sample_chunk_B])
    print("Success:", ans_B["success"])
    print("Answer:", ans_B["answer"])
    print("Used Fallback:", ans_B.get("used_context_fallback"))
    assert ans_B["success"] == False
    assert "temporarily unavailable" in ans_B["answer"]
    
    # Test C (Hallucination check)
    ag.generate_chat_response = mock_gemini_success
    q_C = "national animal of India"
    sample_chunk_C = {
        "chunk_id": "3",
        "text": "Python is a programming language.",
        "source_url": "https://python.org",
        "title": "Python",
        "similarity_score": 0.85
    }
    print(f"\n[Test Case C] Question: '{q_C}' (Grounding check)")
    ans_C = generate_rag_answer(q_C, [sample_chunk_C])
    print("Answer:", ans_C["answer"])
    assert ans_C["answer"] == "I could not find this information in the indexed website."
    
    ag.generate_chat_response = original_generate
    
    print("\n" + "=" * 70)
    print("RAG Answer Generator self-test completed successfully!")
    print("=" * 70)
