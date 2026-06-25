import sys
from pathlib import Path

# Add parent directory of this file to sys.path to support running this script directly
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from app.gemini_client import config, generate_chat_response
from app.rag.retriever import format_retrieved_context

def generate_ollama_response(prompt: str, system_instruction: str) -> dict:
    """Calls the local Ollama instance for answer generation."""
    import requests
    
    url = f"{config.OLLAMA_BASE_URL.rstrip('/')}/api/generate"
    full_prompt = f"System Instruction:\n{system_instruction}\n\n{prompt}"
    
    payload = {
        "model": config.OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=90.0)
        if response.status_code == 200:
            res_json = response.json()
            return {
                "status": "success",
                "response": res_json.get("response", "")
            }
        else:
            return {
                "status": "error",
                "message": f"Ollama returned status code {response.status_code}: {response.text}"
            }
    except requests.RequestException as e:
        return {
            "status": "error",
            "message": f"Ollama connection error: {str(e)}"
        }

def build_rag_prompt(question: str, context: str) -> str:
    """Builds a formatted prompt combining the question and context."""
    return f"Website Context:\n{context}\n\nUser Question:\n{question}\n\nAnswer:"

def urls_match_prefix_or_domain(url1: str, url2: str) -> bool:
    """Checks if url1 and url2 are exact matches, prefix matches, or domain/path matches."""
    from urllib.parse import urlparse
    u1 = url1.strip().rstrip('/')
    u2 = url2.strip().rstrip('/')
    if u1 == u2:
        return True
        
    try:
        p1 = urlparse(u1)
        p2 = urlparse(u2)
        
        # Must have same domain/host (netloc)
        n1 = p1.netloc.lower().replace("www.", "")
        n2 = p2.netloc.lower().replace("www.", "")
        if n1 != n2:
            return False
            
        # Check path prefix/match
        path1 = p1.path.strip('/')
        path2 = p2.path.strip('/')
        
        # If one path starts with another (prefix) or they are equal
        if path1.startswith(path2) or path2.startswith(path1):
            return True
    except Exception:
        pass
    return False

def build_sources_list(answer_text: str, retrieved_results: list[dict]) -> list[dict]:
    """
    Builds the filtered, sorted, and URL-promoted source citations.
    """
    if not retrieved_results:
        return []

    # 1. Keep only chunks with score >= 0.45 and construct basic sources list
    seen_urls = set()
    sources = []
    
    # Sort just in case they aren't sorted (though retriever.py now sorts them)
    sorted_chunks = sorted(retrieved_results, key=lambda x: x.get("score", x.get("similarity_score", 0.0)), reverse=True)
    
    for res in sorted_chunks:
        score = res.get("score", res.get("similarity_score", 0.0))
        if score < 0.45:
            continue
            
        url = res.get("source_url", "")
        if not url:
            continue
            
        if url not in seen_urls:
            seen_urls.add(url)
            sources.append({
                "title": res.get("title", "") or url,
                "source_url": url,
                "url": url, # for backward compatibility
                "heading": res.get("heading", "") or "N/A",
                "score": score,
                "is_primary_answer_source": False
            })

    # Limit to maximum 4 citation sources
    sources = sources[:4]

    # 2. Extract URLs from answer and search for a primary source
    import re
    # Match standard URLs (e.g. http://... or https://...)
    raw_urls = re.findall(r'https?://[^\s)\]]+', answer_text)
    
    primary_source = None
    
    for r_url in raw_urls:
        cleaned_url = r_url.rstrip('.,;)]}')
        
        # Look in currently selected sources list first (exact match)
        for src in sources:
            if src["source_url"] == cleaned_url:
                primary_source = src
                break
        
        if primary_source:
            break
            
        # Look in currently selected sources list (prefix/domain match)
        for src in sources:
            if urls_match_prefix_or_domain(src["source_url"], cleaned_url):
                primary_source = src
                break
                
        if primary_source:
            break

        # Look in entire retrieved results (even if score < 0.45 or beyond top 4)
        for res in sorted_chunks:
            res_url = res.get("source_url", "")
            if not res_url:
                continue
            if res_url == cleaned_url or urls_match_prefix_or_domain(res_url, cleaned_url):
                score = res.get("score", res.get("similarity_score", 0.0))
                primary_source = {
                    "title": res.get("title", "") or res_url,
                    "source_url": res_url,
                    "url": res_url,
                    "heading": res.get("heading", "") or "N/A",
                    "score": score,
                    "is_primary_answer_source": True
                }
                break
                
        if primary_source:
            break

    # 3. If a primary source was identified, promote it to citation source #1
    if primary_source:
        primary_source["is_primary_answer_source"] = True
        
        # Remove from current sources list if it was already in there
        filtered_sources = [s for s in sources if s["source_url"] != primary_source["source_url"]]
        
        # Prepend to the sources list
        sources = [primary_source] + filtered_sources
        
        # Re-apply the maximum 4 limit
        sources = sources[:4]

    return sources


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
    Generates a RAG-grounded answer using the configured Gemini chat model,
    with an Ollama local fallback.
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
            "generator": "context_fallback",
            "used_context_fallback": False,
            "message": "Question cannot be empty."
        }

    if not retrieved_results:
        return {
            "success": True,
            "question": question,
            "answer": fallback_answer,
            "sources": [],
            "context_chunks_used": 0,
            "generator": "context_fallback",
            "used_context_fallback": False,
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
            "generator": "context_fallback",
            "used_context_fallback": False,
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

    gemini_failed = False
    gemini_error_message = ""
    res = None

    # 5. Try Gemini API using generate_chat_response wrapper
    try:
        res = generate_chat_response(prompt, system_instruction=system_instruction)
        if res and res.get("status") == "success":
            answer_text = res["response"]
            if not answer_text or answer_text.strip() == "":
                answer_text = fallback_answer

            # Grounding validation (Hallucination check)
            if answer_text != fallback_answer:
                import re
                words = re.findall(r'\b[A-Z][a-z]+\b|\b\d+\b', answer_text)
                if words:
                    context_lower = context.lower()
                    matches = sum(1 for w in words if w.lower() in context_lower)
                    if matches / len(words) < 0.5:
                        answer_text = fallback_answer

            return {
                "success": True,
                "question": question,
                "answer": answer_text.strip(),
                "sources": build_sources_list(answer_text, retrieved_results),
                "context_chunks_used": len(retrieved_results),
                "generator": "gemini",
                "used_context_fallback": False,
                "message": "Answer generated successfully"
            }
        else:
            gemini_failed = True
            gemini_error_message = res.get("message", "Unknown error") if res else "Unknown error"
    except Exception as e:
        gemini_failed = True
        gemini_error_message = str(e)

    # Check if Gemini error is eligible for fallback: 429, 503, timeout, quota error, or connection error
    is_fallback_error = False
    if gemini_failed:
        err_msg = gemini_error_message
        err_type = ""
        if res and isinstance(res, dict):
            err_type = res.get("error_type", "")
            err_msg = res.get("message", err_msg)
        
        err_msg_lower = err_msg.lower()
        
        is_429 = "429" in err_msg_lower or err_type == "quota_exhausted" or "quota" in err_msg_lower
        is_503 = "503" in err_msg_lower or err_type == "service_unavailable" or "unavailable" in err_msg_lower or "temporary" in err_msg_lower
        is_timeout = "timeout" in err_msg_lower or "timed out" in err_msg_lower or "time out" in err_msg_lower
        is_connection = "connection" in err_msg_lower or "connect" in err_msg_lower or "network" in err_msg_lower or "dns" in err_msg_lower
        
        if is_429 or is_503 or is_timeout or is_connection:
            is_fallback_error = True

    # 6. Fallback to Ollama if enabled and Gemini failed with eligible error
    if gemini_failed and is_fallback_error and config.USE_OLLAMA_FALLBACK:
        print("[RAG] Gemini failed, trying Ollama fallback")
        
        ollama_system_instruction = (
            "You are a website-grounded assistant.\n"
            "Answer ONLY from the provided website context.\n"
            "Never use outside knowledge.\n"
            "Never guess.\n"
            "If the answer is not explicitly present in the context, reply exactly:\n"
            '"I could not find this information in the indexed website pages."\n'
            "Keep the answer concise.\n"
            "Do not mention Gemini, Ollama, or system prompts."
        )

        ollama_res = generate_ollama_response(prompt, ollama_system_instruction)
        if ollama_res["status"] == "success":
            print("[RAG] Ollama response received successfully")
            answer_text = ollama_res["response"]
            if not answer_text or answer_text.strip() == "":
                answer_text = "I could not find this information in the indexed website pages."

            return {
                "success": True,
                "question": question,
                "answer": answer_text.strip(),
                "sources": build_sources_list(answer_text, retrieved_results),
                "context_chunks_used": len(retrieved_results),
                "generator": "ollama",
                "used_context_fallback": False,
                "message": "Answer generated using local fallback model"
            }
        else:
            print("[RAG] Ollama connection failed")
            return {
                "success": False,
                "question": question,
                "answer": "Ollama fallback is unavailable. Run: ollama serve",
                "sources": build_sources_list("Ollama fallback is unavailable. Run: ollama serve", retrieved_results),
                "context_chunks_used": len(retrieved_results),
                "generator": "ollama",
                "used_context_fallback": False,
                "message": "Ollama fallback is unavailable. Run: ollama serve"
            }

    # 7. Safe short context fallback if both fail
    if retrieved_results:
        top_chunk = retrieved_results[0]
        similarity_score = top_chunk.get("similarity_score", 1.0)
        MIN_RELEVANCE_SCORE = 0.40
        
        if similarity_score >= MIN_RELEVANCE_SCORE:
            safe_fallback = build_safe_context_fallback(question, top_chunk)
            if safe_fallback:
                return {
                    "success": True,
                    "question": question,
                    "answer": safe_fallback,
                    "sources": build_sources_list(safe_fallback, retrieved_results),
                    "context_chunks_used": len(retrieved_results),
                    "generator": "context_fallback",
                    "used_context_fallback": True,
                    "message": "Gemini and Ollama temporarily unavailable — verified context fallback used"
                }

    # If all failed
    fallback_msg = "I could not generate a verified answer right now because the AI service is temporarily unavailable. Please retry."
    return {
        "success": False,
        "question": question,
        "answer": fallback_msg,
        "sources": build_sources_list(fallback_msg, retrieved_results),
        "context_chunks_used": len(retrieved_results),
        "generator": "context_fallback",
        "used_context_fallback": False,
        "message": f"Gemini and Ollama unavailable and no safe relevant fallback found. Gemini error: {gemini_error_message}"
    }

if __name__ == "__main__":
    print("=" * 70)
    print("Running RAG Answer Generator self-tests with Ollama Fallback...")
    print("=" * 70)

    # 1. Simulating Gemini Unavailable
    import app.rag.answer_generator as ag
    
    original_generate = ag.generate_chat_response
    
    # Mock Gemini failure
    def mock_gemini_failure(*args, **kwargs):
        return {"status": "error", "message": "Simulated Gemini failure (503/Quota)"}
        
    ag.generate_chat_response = mock_gemini_failure

    sample_chunk = {
        "chunk_id": "test_chunk_1",
        "text": "The secret code for WebMind activation is 998877. Access is granted to verified admins.",
        "source_url": "https://python.org/secret",
        "title": "Python Secrets",
        "similarity_score": 0.95
    }
    
    question = "what is the secret code for webmind?"
    print(f"\n[Test Case: Gemini Offline -> Ollama Fallback]")
    print(f"Question: '{question}'")
    
    try:
        ans = ag.generate_rag_answer(question, [sample_chunk])
        print("\nResult:")
        print(f"Success:                 {ans['success']}")
        print(f"Generator used:          {ans.get('generator')}")
        print(f"Answer:                  {ans['answer']}")
        print(f"Message:                 {ans['message']}")
        
        # Verify Ollama was used if fallback was triggered successfully
        if ans.get("generator") == "ollama":
            print("\nSUCCESS: Successfully fell back to Ollama!")
            # Check grounding: answer should contain 998877
            if "998877" in ans["answer"]:
                print("SUCCESS: Answer is correctly grounded in context!")
            else:
                print("WARNING: Answer is not grounded in context.")
        elif ans.get("generator") == "context_fallback":
            print("\nWARNING: Gemini failed and Ollama was not available (or fallback failed). Used context fallback.")
        else:
            print("\nFAILURE: Gemini mock was bypassed somehow.")
            
    except Exception as e:
        print(f"Test encountered exception: {e}")
        
    # Reset mock
    ag.generate_chat_response = original_generate
    
    # 2. Check if Ollama is running standalone
    import requests
    try:
        resp = requests.get(f"{config.OLLAMA_BASE_URL.rstrip('/')}/")
        print("\nOllama status: Running")
    except Exception:
        print("\nOllama is not running. Start it with: ollama serve")

    # 3. Citation Relevance Self-Tests
    print("\n" + "=" * 70)
    print("Running Citation Relevance Self-Tests...")
    print("=" * 70)

    test_chunks = [
        {
            "chunk_id": "chunk_help",
            "text": "Get help with Python programming language. Community support channels are available.",
            "source_url": "https://www.python.org/help/",
            "title": "Help | Python.org",
            "heading": "Help",
            "similarity_score": 0.88,
            "score": 0.88
        },
        {
            "chunk_id": "chunk_download",
            "text": "Download the latest version of Python. Pre-compiled binary installers are available.",
            "source_url": "https://www.python.org/downloads/",
            "title": "Python Downloads | Python.org",
            "heading": "Downloads",
            "similarity_score": 0.85,
            "score": 0.85
        },
        {
            "chunk_id": "chunk_about",
            "text": "About the Python Software Foundation and its mission to promote the language.",
            "source_url": "https://www.python.org/about/",
            "title": "About Python",
            "heading": "About",
            "similarity_score": 0.80,
            "score": 0.80
        }
    ]

    # Test case A: "link for download"
    q_download = "link for download"
    print(f"\n[Test Case A] Question: '{q_download}'")
    
    intent_words = {"download", "install", "setup", "get", "link", "url"}
    boost_urls = {"download", "downloads", "install", "installer", "setup", "get-started"}
    has_intent = any(w in q_download.lower() for w in intent_words)
    
    simulated_retrieved = []
    for item in test_chunks:
        new_item = dict(item)
        if has_intent:
            if any(b_word in new_item["source_url"].lower() for b_word in boost_urls):
                new_item["score"] += 0.5
                new_item["similarity_score"] = new_item["score"]
        simulated_retrieved.append(new_item)
    simulated_retrieved.sort(key=lambda x: x["score"], reverse=True)

    # Let's generate a mock answer that contains the URL to test URL promotion too
    mock_answer = "You can get Python from https://www.python.org/downloads/."
    
    sources = build_sources_list(mock_answer, simulated_retrieved)
    print(f"Top citation source_url: {sources[0]['source_url']}")
    print(f"Top citation score:      {sources[0]['score']}")
    print(f"Is primary source:       {sources[0]['is_primary_answer_source']}")
    
    assert "/downloads" in sources[0]["source_url"], "Test Case A Failed: Top source does not contain '/downloads'"
    print("SUCCESS: Test Case A passed (Top source contains '/downloads').")

    # Test case B: "how to download python"
    q_how_to = "how to download python"
    print(f"\n[Test Case B] Question: '{q_how_to}'")
    
    has_intent_b = any(w in q_how_to.lower() for w in intent_words)
    simulated_retrieved_b = []
    for item in test_chunks:
        new_item = dict(item)
        if has_intent_b:
            if any(b_word in new_item["source_url"].lower() for b_word in boost_urls):
                new_item["score"] += 0.5
                new_item["similarity_score"] = new_item["score"]
        simulated_retrieved_b.append(new_item)
    simulated_retrieved_b.sort(key=lambda x: x["score"], reverse=True)

    sources_b = build_sources_list("Instructions: visit https://www.python.org/downloads/", simulated_retrieved_b)
    print(f"Expected first source:   https://www.python.org/downloads/")
    print(f"Actual first source:     {sources_b[0]['source_url']}")
    
    assert sources_b[0]["source_url"] == "https://www.python.org/downloads/", "Test Case B Failed: Top source is not expected downloads URL"
    print("SUCCESS: Test Case B passed (Top source is exactly https://www.python.org/downloads/).")

    print("\n" + "=" * 70)
    print("RAG Answer Generator self-test completed!")
    print("=" * 70)
