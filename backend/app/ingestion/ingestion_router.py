import sys
from pathlib import Path

# Add the parent directory of this file to sys.path to support direct execution
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from app.ingestion.url_validator import validate_url
from app.ingestion.content_type_detector import detect_content_type
from app.ingestion.html_ingestor import ingest_html
from app.ingestion.pdf_ingestor import ingest_pdf
from app.ingestion.json_ingestor import ingest_json

def ingest_url(url: str) -> dict:
    """
    Orchestrates the document ingestion pipeline:
    1. Validates the URL safely against SSRF loopback/private hosts.
    2. Lightweight checks to detect the Content-Type (HEAD-first).
    3. Routes the resolved URL target to the appropriate ingestor module:
       - 'html' -> app.ingestion.html_ingestor.ingest_html()
       - 'pdf' -> app.ingestion.pdf_ingestor.ingest_pdf()
       - 'json' -> app.ingestion.json_ingestor.ingest_json()
       - 'text' -> Returns plain text warning message.
       - 'unsupported' -> Returns unsupported message.
    """
    # 1. Validate target URL
    validation = validate_url(url)
    if not validation["valid"]:
        return create_router_failure_response(
            url, 
            error_message=f"URL validation failed: {validation['message']}"
        )

    normalized_url = validation["normalized_url"]

    # 2. Detect Content Type
    type_detection = detect_content_type(normalized_url)
    if not type_detection["success"]:
        return create_router_failure_response(
            normalized_url, 
            error_message=f"Content type detection failed: {type_detection['message']}"
        )

    content_type = type_detection["content_type"]
    target_url = type_detection["final_url"]

    # 3. Route by type
    if content_type == "html":
        result = ingest_html(target_url)
        result["content_type"] = "html"
        return result
    elif content_type == "pdf":
        result = ingest_pdf(target_url)
        result["content_type"] = "pdf"
        return result
    elif content_type == "json":
        result = ingest_json(target_url)
        result["content_type"] = "json"
        return result
    elif content_type == "text":
        return {
            "success": False,
            "final_url": target_url,
            "content_type": "text",
            "title": "",
            "description": "",
            "headings": [],
            "text": "",
            "combined_text": "",
            "links": [],
            "pages": [],
            "page_count": 0,
            "data": {},
            "text_length": 0,
            "message": "Plain text ingestion will be added later"
        }
    else:
        raw_header = type_detection.get("raw_content_type", "unknown")
        return {
            "success": False,
            "final_url": target_url,
            "content_type": "unsupported",
            "title": "",
            "description": "",
            "headings": [],
            "text": "",
            "combined_text": "",
            "links": [],
            "pages": [],
            "page_count": 0,
            "data": {},
            "text_length": 0,
            "message": f"Unsupported content type mapping: '{raw_header}'"
        }

def create_router_failure_response(url: str, error_message: str) -> dict:
    """Helper to structure router failure results consistently."""
    return {
        "success": False,
        "final_url": url,
        "content_type": "unknown",
        "title": "",
        "description": "",
        "headings": [],
        "text": "",
        "combined_text": "",
        "links": [],
        "pages": [],
        "page_count": 0,
        "data": {},
        "text_length": 0,
        "message": error_message
    }

if __name__ == "__main__":
    test_pdf = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    test_json = "https://api.github.com"

    print("=" * 70)
    print("Running Ingestion Router self-tests...")
    print("=" * 70)

    # 1. Run PDF route test
    print(f"\n[Test 1] Routing PDF link: {test_pdf}")
    pdf_result = ingest_url(test_pdf)
    if pdf_result["success"]:
        print("  SUCCESS!")
        print(f"  Content Type: {pdf_result.get('content_type')}")
        print(f"  Title:        {pdf_result.get('title')}")
        print(f"  Page Count:   {pdf_result.get('page_count')}")
        print(f"  Text preview: {pdf_result.get('combined_text')[:150].strip()}...")
    else:
        print(f"  FAILED: {pdf_result['message']}")

    # 2. Run JSON route test
    print(f"\n[Test 2] Routing JSON endpoint: {test_json}")
    json_result = ingest_url(test_json)
    if json_result["success"]:
        print("  SUCCESS!")
        print(f"  Content Type: {json_result.get('content_type')}")
        print(f"  Text Length:  {json_result.get('text_length')} chars")
        print(f"  Text preview: {json_result.get('text')[:150].strip()}...")
    else:
        print(f"  FAILED: {json_result['message']}")

    print("\n" + "=" * 70)
    print("Self-tests completed!")
    print("=" * 70)
