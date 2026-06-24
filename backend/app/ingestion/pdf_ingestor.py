import io
import sys
import requests
from pathlib import Path
from urllib.parse import urlparse
from pypdf import PdfReader
from requests.exceptions import Timeout, ConnectionError, SSLError, HTTPError

# Add parent directory of this file to sys.path to run this script directly
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

def ingest_pdf(url: str) -> dict:
    """
    Downloads and extracts text from a remote PDF document.
    - Limits downloading to maximum 20 MB size.
    - Limits processing to maximum 100 pages.
    - Limits extracted combined text to 200,000 characters.
    - Disallows password-protected files.
    - Handles invalid format and connection errors gracefully.
    """
    headers = {
        "User-Agent": "WebMind-RAG-Bot/1.0"
    }
    timeout = 30
    
    # 1. Download target PDF with chunk size limits
    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
        response.raise_for_status()
        
        # Check Content-Length header if available
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > 20 * 1024 * 1024:
            return create_failure_response("File size exceeds the 20 MB limit.")
            
        # Download and measure chunks to prevent oversize memory consumption
        pdf_bytes = bytearray()
        total_downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            total_downloaded += len(chunk)
            if total_downloaded > 20 * 1024 * 1024:
                return create_failure_response("File size exceeds the 20 MB limit.")
            pdf_bytes.extend(chunk)
            
    except Timeout:
        return create_failure_response("Connection timed out after 30 seconds.")
    except ConnectionError:
        return create_failure_response("Connection error: PDF host server could not be reached.")
    except SSLError:
        return create_failure_response("SSL certificate verification failed.")
    except HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        return create_failure_response(f"HTTP error occurred: {str(e)}", status_code=status)
    except Exception as e:
        return create_failure_response(f"An unexpected request error occurred: {str(e)}")

    final_url = response.url

    # Generate title from path
    parsed_url = urlparse(final_url)
    title = parsed_url.path.split('/')[-1]
    if not title or not title.lower().endswith('.pdf'):
        title = "document.pdf"

    # 2. Parse PDF contents using pypdf
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
    except Exception as e:
        return create_failure_response(f"Invalid PDF structure or file corruption: {str(e)}")

    # Check for encryption
    if reader.is_encrypted:
        return create_failure_response("Password-protected PDFs are not supported.")

    pages = []
    combined_text_list = []
    max_pages = 100
    max_text_chars = 200000

    page_count = len(reader.pages)
    pages_to_process = min(page_count, max_pages)

    # 3. Extract text page-by-page
    for idx in range(pages_to_process):
        try:
            page = reader.pages[idx]
            page_text = page.extract_text() or ""
            
            # Clean line formatting: collapse extra spaces, strip whitespace
            cleaned_lines = []
            for line in page_text.splitlines():
                stripped = " ".join(line.split())
                if stripped:
                    cleaned_lines.append(stripped)
            cleaned_page_text = "\n".join(cleaned_lines)
            
            pages.append({
                "page_number": idx + 1,
                "text": cleaned_page_text
            })
            combined_text_list.append(cleaned_page_text)
            
        except Exception as e:
            pages.append({
                "page_number": idx + 1,
                "text": f"[Error extracting page text: {str(e)}]"
            })

    combined_text = "\n".join(combined_text_list)
    if len(combined_text) > max_text_chars:
        combined_text = combined_text[:max_text_chars]

    return {
        "success": True,
        "final_url": final_url,
        "title": title,
        "pages": pages,
        "combined_text": combined_text,
        "page_count": page_count,
        "text_length": len(combined_text),
        "message": "PDF content extracted successfully"
    }

def create_failure_response(error_message: str, status_code: int = None) -> dict:
    """Helper to structure failure responses consistently."""
    msg = f"{error_message} (Status Code: {status_code})" if status_code else error_message
    return {
        "success": False,
        "final_url": None,
        "title": "",
        "pages": [],
        "combined_text": "",
        "page_count": 0,
        "text_length": 0,
        "message": msg
    }

if __name__ == "__main__":
    test_pdf_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    print("=" * 70)
    print(f"Running PDF Ingestor self-test on: {test_pdf_url}")
    print("=" * 70)

    result = ingest_pdf(test_pdf_url)
    if result["success"]:
        print("\n SUCCESS!")
        print(f"Final URL:   {result['final_url']}")
        print(f"Title:       {result['title']}")
        print(f"Pages:       {result['page_count']}")
        print(f"Text Length: {result['text_length']} chars")
        
        print("\nPage List:")
        for pg in result["pages"]:
            print(f"  - Page {pg['page_number']}: {len(pg['text'])} chars")
            
        print("\nCombined Text preview (first 300 chars):")
        print("-" * 50)
        print(result["combined_text"][:300] + "\n...")
        print("-" * 50)
    else:
        print("\n FAILURE!")
        print(f"Message: {result['message']}")

    print("\n" + "=" * 70)
    print("Self-test completed!")
    print("=" * 70)
