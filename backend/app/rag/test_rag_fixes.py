import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.rag.answer_generator import (
    is_short_topic_query,
    clean_text_for_summary,
    build_clean_fallback_summary,
    is_not_found_response,
    generate_rag_answer
)

def run_tests():
    print("=" * 60)
    print("Running Unit Tests for WebMind RAG Fixes...")
    print("=" * 60)

    # Test 1: is_short_topic_query
    print("\n[Test 1] Testing is_short_topic_query...")
    assert is_short_topic_query("dsa tutorial") is True
    assert is_short_topic_query("array structure overview") is True
    assert is_short_topic_query("python") is True
    assert is_short_topic_query("what is dsa?") is False
    assert is_short_topic_query("how to code in python?") is False
    assert is_short_topic_query("can you explain recursion?") is False
    assert is_short_topic_query("this is a very long sentence that has more than four words") is False
    print(" -> SUCCESS: is_short_topic_query behaves correctly.")

    # Test 2: clean_text_for_summary
    print("\n[Test 2] Testing clean_text_for_summary...")
    dirty_text = (
        "Home\n"
        "Menu\n"
        "≡ Main navigation\n"
        "DSA Tutorial - GeeksforGeeksCoursesTutorialsPracticeJobsDSA Tutorial\n"
        "Last Updated : 20 May, 2026\n"
        "DSA stands for Data Structures and Algorithms. Data structures manage how data is stored and accessed.\n"
        "Algorithms focus on processing this data. They solve problems efficiently.\n"
        "Contact Us\n"
        "All rights reserved Copyright 2026"
    )
    cleaned = clean_text_for_summary(dirty_text)
    print(f"Original Text snippet:\n{dirty_text[:120]}...")
    print(f"Cleaned Text:\n'{cleaned}'")
    # Verify that clean_text_for_summary successfully extracted the core explanation sentences
    assert "DSA stands for Data Structures" in cleaned
    assert "Algorithms focus on processing" in cleaned
    assert "Home" not in cleaned
    assert "Menu" not in cleaned
    assert "Copyright" not in cleaned
    print(" -> SUCCESS: clean_text_for_summary successfully removes navigation noise and extracts paragraph content.")

    # Test 3: is_not_found_response
    print("\n[Test 3] Testing is_not_found_response...")
    assert is_not_found_response("I could not find this information in the indexed website pages.") is True
    assert is_not_found_response("I could not find anything about it.") is True
    assert is_not_found_response("") is True
    assert is_not_found_response("DSA is an acronym for Data Structures and Algorithms.") is False
    print(" -> SUCCESS: is_not_found_response identifies rejections properly.")

    # Test 4: generate_rag_answer relevance threshold guard
    print("\n[Test 4] Testing generate_rag_answer relevance threshold guard...")
    
    mock_chunks_low_relevance = [
        {
            "chunk_id": "c1",
            "text": "Random irrelevant text about dogs and cats.",
            "source_url": "https://example.com/cats",
            "title": "Irrelevant Page",
            "similarity_score": 0.20,
            "score": 0.20
        }
    ]
    
    # Under low relevance, it should return the not-found fallback without querying the LLM
    result_low = generate_rag_answer("dsa tutorial", mock_chunks_low_relevance)
    assert result_low["answer_mode"] == "not_found"
    assert result_low["retrieval_relevant"] is False
    assert "could not find information" in result_low["answer"]
    print(" -> SUCCESS: Relevance guard correctly blocks low scoring chunks and returns not-found fallback.")

    # Test 5: generate_rag_answer rejection guard (LLM false negative)
    print("\n[Test 5] Testing generate_rag_answer rejection guard...")
    
    mock_chunks_high_relevance = [
        {
            "chunk_id": "c2",
            "text": "DSA stands for Data Structures and Algorithms. Data structures manage how data is stored and accessed.",
            "source_url": "https://example.com/dsa",
            "title": "DSA Tutorial",
            "similarity_score": 0.90,
            "score": 0.90
        }
    ]
    
    # We will temporarily mock generate_chat_response to return a "not found" response
    import app.rag.answer_generator as ag
    original_generate = ag.generate_chat_response
    
    try:
        # Simulate LLM returning a false negative rejection
        ag.generate_chat_response = lambda prompt, system_instruction=None: {
            "status": "success",
            "response": "I could not find this information in the indexed website pages."
        }
        
        result_high = ag.generate_rag_answer("dsa tutorial", mock_chunks_high_relevance)
        print(f"Rejection guard response: '{result_high['answer']}'")
        assert result_high["answer_mode"] == "context_fallback"
        assert result_high["retrieval_relevant"] is True
        assert result_high["used_context_fallback"] is True
        assert "DSA stands for Data Structures" in result_high["answer"]
        print(" -> SUCCESS: Rejection guard successfully intercepts LLM rejections and uses clean fallback summary.")
    finally:
        ag.generate_chat_response = original_generate

    print("\n" + "=" * 60)
    print("ALL UNIT TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
