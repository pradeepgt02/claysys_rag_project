import uuid
import sys
import requests
from pathlib import Path

# Add parent directory of this file to sys.path to run this script directly
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from app.extractors.content_cleaner import clean_text
from app.extractors.extraction_router import extract_structured_content

def chunk_text(
    text: str,
    source_url: str,
    title: str = "",
    heading: str = "",
    content_type: str = "html",
    page_number: int | None = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 150
) -> list[dict]:
    """
    Cleans and splits a block of text into meaningful chunks, prioritizing split points
    near sentence endings ('.', '!', '?', newline).
    
    Requirements:
    - Automatically cleans text using clean_text.
    - Limits/guards against invalid chunk_size and chunk_overlap values.
    - Prevents word splitting by scanning backward within a search window.
    - Skips chunks shorter than 50 characters, unless it is the only chunk.
    - Attaches detailed metadata to each chunk.
    
    Returns a list of chunk dictionaries.
    """
    # 1. Clean the text using the existing clean_text utility
    text = clean_text(text)
    if not text:
        return []

    # 2. Input validation and boundary safety
    if chunk_size <= 0:
        chunk_size = 1000
    if chunk_overlap < 0:
        chunk_overlap = 0
    if chunk_overlap >= chunk_size:
        chunk_overlap = chunk_size // 2

    text_len = len(text)

    # 3. Simple case: if text is smaller than chunk_size, return single chunk
    if text_len <= chunk_size:
        return [{
            "chunk_id": str(uuid.uuid4()),
            "text": text,
            "source_url": source_url,
            "title": title,
            "heading": heading,
            "content_type": content_type,
            "page_number": page_number,
            "chunk_index": 0,
            "char_start": 0,
            "char_end": text_len
        }]

    # 4. Sliding window chunking
    chunks = []
    start = 0
    chunk_index = 0

    while start < text_len:
        end = start + chunk_size

        # If the window extends past the text end, grab remaining text
        if end >= text_len:
            end = text_len
            chunk_slice = text[start:end]
            if len(chunk_slice) >= 50 or chunk_index == 0:
                chunks.append({
                    "chunk_id": str(uuid.uuid4()),
                    "text": chunk_slice,
                    "source_url": source_url,
                    "title": title,
                    "heading": heading,
                    "content_type": content_type,
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                    "char_start": start,
                    "char_end": end
                })
            break

        # Search window for sentence boundaries (from end back to start + chunk_overlap)
        # We look in the latter part of the chunk (up to 1/3 of size, or overlap size)
        search_window_size = max(chunk_size // 3, chunk_overlap)
        search_min = max(start + chunk_overlap, end - search_window_size)
        slice_to_search = text[search_min:end]

        split_point = end
        found_separator = False

        # Find sentence boundaries: newlines or periods/punctuation followed by space
        for sep in ["\n", ". ", "! ", "? "]:
            r_idx = slice_to_search.rfind(sep)
            if r_idx != -1:
                # Include the separator character(s) in the current chunk
                split_point = search_min + r_idx + len(sep)
                found_separator = True
                break

        # Fallback: if no punctuation, search for space to avoid splitting words
        if not found_separator:
            r_idx = slice_to_search.rfind(" ")
            if r_idx != -1:
                split_point = search_min + r_idx + 1

        # Extract chunk text slice
        chunk_slice = text[start:split_point]

        # Add chunk if it meets size requirements
        if len(chunk_slice) >= 50 or chunk_index == 0:
            chunks.append({
                "chunk_id": str(uuid.uuid4()),
                "text": chunk_slice,
                "source_url": source_url,
                "title": title,
                "heading": heading,
                "content_type": content_type,
                "page_number": page_number,
                "chunk_index": chunk_index,
                "char_start": start,
                "char_end": split_point
            })
            chunk_index += 1

        # Determine next start position
        next_start = split_point - chunk_overlap
        
        # Prevent infinite loops due to degenerate boundaries
        if next_start <= start:
            next_start = start + (chunk_size - chunk_overlap)

        start = next_start

    return chunks

def chunk_document(
    document: dict,
    chunk_size: int = 1000,
    chunk_overlap: int = 150
) -> list[dict]:
    """
    Accepts a standard document structure:
    {
      "url": "...",
      "title": "...",
      "text": "...",
      "content_type": "html",
      "headings": [...]
    }
    And parses it using chunk_text.
    """
    if not document:
        return []

    url = document.get("url", "") or document.get("final_url", "")
    title = document.get("title", "")
    text = document.get("text", "")
    content_type = document.get("content_type", "html")

    return chunk_text(
        text=text,
        source_url=url,
        title=title,
        content_type=content_type,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )

def chunk_pdf_pages(
    pdf_result: dict,
    source_url: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 150
) -> list[dict]:
    """
    Accepts the return output from app/ingestion/pdf_ingestor.py.
    Chunks each PDF page separately, preserving the page_number attribute
    in the metadata. Generates sequential global chunk indices across pages.
    """
    if not pdf_result or not pdf_result.get("success", False):
        return []

    pages = pdf_result.get("pages", [])
    if not pages:
        return []

    title = pdf_result.get("title", "document.pdf")
    all_chunks = []

    for page in pages:
        page_num = page.get("page_number")
        page_text = page.get("text", "")

        # Chunk the page text
        page_chunks = chunk_text(
            text=page_text,
            source_url=source_url,
            title=title,
            content_type="pdf",
            page_number=page_num,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        all_chunks.extend(page_chunks)

    # Re-index chunks globally so they run sequentially [0, 1, 2, ...] for the entire file
    for idx, chunk in enumerate(all_chunks):
        chunk["chunk_index"] = idx

    return all_chunks

if __name__ == "__main__":
    print("=" * 70)
    print("Running Text Chunker self-test on: https://fastapi.tiangolo.com/")
    print("=" * 70)

    target_url = "https://fastapi.tiangolo.com/"
    print(f"Downloading: {target_url}")

    try:
        response = requests.get(
            target_url,
            headers={"User-Agent": "WebMind-RAG-Bot/1.0"},
            timeout=15,
            allow_redirects=True
        )
        response.raise_for_status()
        html_content = response.text
        print(f"Download complete. Parsing structures...")

        # Parse content
        extracted = extract_structured_content(html_content)
        cleaned_text = extracted.get("clean_text", "")
        print(f"Original Cleaned Text Length: {len(cleaned_text)} characters.")

        # Chunk content
        chunk_size = 800
        chunk_overlap = 120
        print(f"Splitting text with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}...")
        chunks = chunk_text(
            text=cleaned_text,
            source_url=target_url,
            title=extracted["metadata"].get("title", "FastAPI"),
            content_type="html",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

        print(f"\n SUCCESS! Created {len(chunks)} chunks.")
        print("-" * 50)
        
        # Print details of the first 3 chunks
        display_limit = min(3, len(chunks))
        for i in range(display_limit):
            chk = chunks[i]
            print(f"Chunk Index:  {chk['chunk_index']}")
            print(f"Chunk ID:     {chk['chunk_id']}")
            print(f"Text Length:  {len(chk['text'])} chars")
            print(f"Source URL:   {chk['source_url']}")
            print(f"Range:        [{chk['char_start']} : {chk['char_end']}]")
            print("Preview:")
            print("  " + chk["text"][:250].replace("\n", "\n  ") + "...")
            print("-" * 50)

    except Exception as e:
        print(f"Error during self-test execution: {e}")
