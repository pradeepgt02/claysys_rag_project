import sys
from pathlib import Path

# Add parent directory of this file to sys.path to support running this script directly
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from app import config
from app.rag.retriever import format_retrieved_context

from app.services.llm_service import generate_answer

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

    # 1. Keep only chunks with score >= config.RAG_MIN_RELEVANCE_SCORE and construct basic sources list
    seen_urls = set()
    sources = []
    
    # Sort just in case they aren't sorted (though retriever.py now sorts them)
    sorted_chunks = sorted(retrieved_results, key=lambda x: x.get("score", x.get("similarity_score", 0.0)), reverse=True)
    
    for res in sorted_chunks:
        score = res.get("score", res.get("similarity_score", 0.0))
        if score < config.RAG_MIN_RELEVANCE_SCORE:
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

    # 2. Extract URLs from answer and search for primary sources
    import re
    # Match standard URLs (e.g. http://... or https://...)
    raw_urls = re.findall(r'https?://[^\s)\]]+', answer_text)
    
    primary_sources = []
    seen_primary_urls = set()
    
    for r_url in raw_urls:
        cleaned_url = r_url.rstrip('.,;)}')
        
        # Look in entire retrieved results
        for res in sorted_chunks:
            res_url = res.get("source_url", "")
            if not res_url:
                continue
            if res_url == cleaned_url or urls_match_prefix_or_domain(res_url, cleaned_url):
                if res_url not in seen_primary_urls:
                    score = res.get("score", res.get("similarity_score", 0.0))
                    primary_sources.append({
                        "title": res.get("title", "") or res_url,
                        "source_url": res_url,
                        "url": res_url,
                        "heading": res.get("heading", "") or "N/A",
                        "score": score,
                        "is_primary_answer_source": True
                    })
                    seen_primary_urls.add(res_url)
                break
                
    # 3. If any primary sources were identified, return ONLY those (max 4)
    if primary_sources:
        return primary_sources[:4]

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

def is_short_topic_query(question: str) -> bool:
    """
    Detects short topic overview queries (1 to 4 words) that do not begin
    with common question words.
    """
    question_clean = question.strip().lower().rstrip("?").strip()
    if not question_clean:
        return False
    words = question_clean.split()
    if 1 <= len(words) <= 4:
        question_words = {"what", "why", "how", "when", "where", "who", "which", "can", "does", "is", "are"}
        if words[0] not in question_words:
            return True
    return False

def clean_text_for_summary(text: str) -> str:
    """
    Cleans top chunk text by removing navigation items, menus, footers, JS/CSS, and HTML tags.
    """
    import re
    if not text:
        return ""
    
    # Remove HTML comments and raw tags
    text = re.sub(r'<!--.*?-->', ' ', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    
    lines = text.split('\n')
    cleaned_lines = []
    
    # Exclude common navigation/menu list items
    nav_keywords = {
        "home", "menu", "search", "sign in", "sign up", "login", "register",
        "cart", "checkout", "practice", "jobs", "courses", "tutorials", "donate",
        "share", "last updated", "socialize", "newsletter", "terms of use", "privacy policy",
        "cookies", "about us", "contact us", "all rights reserved", "copyright"
    }
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        if line_str.lower() in nav_keywords:
            continue
        
        # Exclude JS/CSS blocks
        if "{" in line_str or "}" in line_str or "const " in line_str or "function()" in line_str:
            continue
            
        words = line_str.split()
        if len(words) < 5:
            continue
            
        # Remove consecutive duplicated spaces
        line_str = re.sub(r'\s+', ' ', line_str)
        cleaned_lines.append(line_str)
        
    full_text = " ".join(cleaned_lines)
    # Remove characters common in menu lists
    full_text = re.sub(r'[≡|•»›]', ' ', full_text)
    full_text = re.sub(r'\s+', ' ', full_text).strip()
    
    sentences = re.split(r'(?<=[.!?])\s+', full_text)
    valid_sentences = []
    for s in sentences:
        s_clean = s.strip()
        if len(s_clean.split()) >= 6:
            # Skip if it is a list of links (e.g. capitalized word ratio is very high)
            capital_ratio = sum(1 for w in s_clean.split() if w and w[0].isupper()) / len(s_clean.split())
            if capital_ratio < 0.6:
                valid_sentences.append(s_clean)
                if len(valid_sentences) >= 3:
                    break
                    
    return " ".join(valid_sentences)

def build_clean_fallback_summary(top_chunk: dict) -> str:
    """
    Summarizes only the top retrieved chunk safely.
    """
    title = top_chunk.get("title") or "the indexed website"
    cleaned = clean_text_for_summary(top_chunk.get("text", ""))
    if cleaned:
        return f"Based on the indexed page '{title}': {cleaned}"
    else:
        raw_text = top_chunk.get("text", "")
        # Fallback to plain truncated text if cleaning was too strict
        snippet = raw_text[:200] + "..." if len(raw_text) > 200 else raw_text
        return f"Based on the indexed page '{title}': {snippet}"

def is_not_found_response(text: str) -> bool:
    """
    Determines if the LLM output is a not-found fallback response.
    """
    clean_text = text.strip().lower().rstrip(".")
    if "could not find this information" in clean_text or "i could not find" in clean_text:
        return True
    if not clean_text:
        return True
    return False

def generate_rag_answer(
    question: str,
    retrieved_results: list[dict]
) -> dict:
    """
    Generates a RAG-grounded answer using Groq.
    """
    fallback_answer = "I could not find this information in the indexed website pages."

    best_score = 0.0
    best_distance = 0.0
    if retrieved_results:
        best_chunk = retrieved_results[0]
        best_score = best_chunk.get("score", best_chunk.get("similarity_score", 0.0))
        best_distance = best_chunk.get("distance", 0.0)

    # 1. Retrieval Guard based on similarity score < config.RAG_MIN_RELEVANCE_SCORE
    threshold = 0.05 if is_short_topic_query(question) else config.RAG_MIN_RELEVANCE_SCORE
    if best_score < threshold:
        return {
            "success": True,
            "question": question,
            "answer": fallback_answer,
            "sources": [],
            "context_chunks_used": len(retrieved_results),
            "generator": "retrieval_guard",
            "used_context_fallback": False,
            "message": f"Top similarity score {best_score} < threshold {threshold}",
            "top_relevance_score": best_score,
            "retrieval_relevant": False,
            "answer_mode": "not_found",
            "is_grounded": False
        }

    # 2. Input validation: Question cannot be empty
    if not question or question.strip() == "":
        return {
            "success": False,
            "question": "",
            "answer": fallback_answer,
            "sources": [],
            "context_chunks_used": 0,
            "generator": "context_fallback",
            "used_context_fallback": False,
            "message": "Question cannot be empty.",
            "top_relevance_score": best_score,
            "retrieval_relevant": False,
            "answer_mode": "not_found",
            "is_grounded": False
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
            "generator": "retrieval_guard",
            "used_context_fallback": False,
            "message": "Retrieved context is empty.",
            "top_relevance_score": best_score,
            "retrieval_relevant": False,
            "answer_mode": "not_found",
            "is_grounded": False
        }

    answer_text, generator_name = generate_answer(question, context)
    
    if answer_text and not answer_text.startswith("AI generation is temporarily unavailable."):
        answer_mode = "not_found" if is_not_found_response(answer_text) else "llm"
        is_grounded = (answer_mode != "not_found")
        sources_list = build_sources_list(answer_text, retrieved_results) if is_grounded else []

        return {
            "success": True,
            "question": question,
            "answer": answer_text.strip(),
            "sources": sources_list,
            "context_chunks_used": len(retrieved_results),
            "generator": generator_name,
            "used_context_fallback": False,
            "message": "Answer generated successfully",
            "top_relevance_score": best_score,
            "retrieval_relevant": True,
            "answer_mode": answer_mode,
            "is_grounded": is_grounded
        }
    else:
        # For extractive fallback, we always show the retrieved references
        sources_list = build_sources_list(answer_text, retrieved_results)
        return {
            "success": True,
            "question": question,
            "answer": answer_text,
            "sources": sources_list,
            "context_chunks_used": len(retrieved_results),
            "generator": generator_name,
            "used_context_fallback": False,
            "message": "LLM providers failed, using extractive fallback.",
            "top_relevance_score": best_score,
            "retrieval_relevant": True,
            "answer_mode": "not_found",
            "is_grounded": False
        }

if __name__ == "__main__":
    print("=" * 70)
    print("Running RAG Answer Generator self-tests with Groq Fallback...")
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
    print(f"\n[Test Case: Gemini Offline -> Groq Fallback]")
    print(f"Question: '{question}'")
    
    try:
        ans = ag.generate_rag_answer(question, [sample_chunk])
        print("\nResult:")
        print(f"Success:                 {ans['success']}")
        print(f"Generator used:          {ans.get('generator')}")
        print(f"Answer:                  {ans['answer']}")
        print(f"Message:                 {ans['message']}")
        
        # Verify Groq was used if fallback was triggered successfully
        if ans.get("generator") == "groq":
            print("\nSUCCESS: Successfully fell back to Groq!")
            # Check grounding: answer should contain 998877
            if "998877" in ans["answer"]:
                print("SUCCESS: Answer is correctly grounded in context!")
            else:
                print("WARNING: Answer is not grounded in context.")
        elif ans.get("generator") == "system":
            print("\nWARNING: Gemini failed and Groq was not available (or fallback failed). Used system fallback.")
        else:
            print("\nFAILURE: Gemini mock was bypassed somehow.")
            
    except Exception as e:
        print(f"Test encountered exception: {e}")
        
    # Reset mock
    ag.generate_chat_response = original_generate

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
