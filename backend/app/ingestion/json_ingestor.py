import json
import sys
import requests
from pathlib import Path
from requests.exceptions import Timeout, ConnectionError, SSLError, HTTPError

# Add parent directory of this file to sys.path to run this script directly
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

def ingest_json(url: str) -> dict:
    """
    Downloads and formats text from a remote JSON endpoint.
    - Limits downloading to maximum 5 MB size.
    - Converts parsed data structures to a readable indented string.
    - Limits final string to 100,000 characters.
    - Handles invalid format and connection errors gracefully.
    """
    headers = {
        "User-Agent": "WebMind-RAG-Bot/1.0"
    }
    timeout = 20
    
    # 1. Download target JSON with size limit checks
    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
        response.raise_for_status()
        
        # Check Content-Length header if available
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > 5 * 1024 * 1024:
            return create_failure_response("File size exceeds the 5 MB limit.")
            
        # Download and measure chunks to prevent memory blowup
        json_bytes = bytearray()
        total_downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            total_downloaded += len(chunk)
            if total_downloaded > 5 * 1024 * 1024:
                return create_failure_response("File size exceeds the 5 MB limit.")
            json_bytes.extend(chunk)
            
    except Timeout:
        return create_failure_response("Connection timed out after 20 seconds.")
    except ConnectionError:
        return create_failure_response("Connection error: JSON host server could not be reached.")
    except SSLError:
        return create_failure_response("SSL certificate verification failed.")
    except HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        return create_failure_response(f"HTTP error occurred: {str(e)}", status_code=status)
    except Exception as e:
        return create_failure_response(f"An unexpected request error occurred: {str(e)}")

    final_url = response.url

    # 2. Parse and format JSON contents
    try:
        # Decode and load bytes structure
        decoded_content = json_bytes.decode('utf-8')
        parsed_data = json.loads(decoded_content)
    except Exception as e:
        return create_failure_response(f"Failed to parse content as valid JSON: {str(e)}")

    # Format JSON to structured pretty text
    try:
        formatted_text = json.dumps(parsed_data, indent=2, ensure_ascii=False)
        
        # Safe character length limit
        if len(formatted_text) > 100000:
            formatted_text = formatted_text[:100000]
    except Exception as e:
        return create_failure_response(f"JSON formatting error: {str(e)}")

    return {
        "success": True,
        "final_url": final_url,
        "data": parsed_data,
        "text": formatted_text,
        "text_length": len(formatted_text),
        "message": "JSON content extracted successfully"
    }

def create_failure_response(error_message: str, status_code: int = None) -> dict:
    """Helper to structure failure responses consistently."""
    msg = f"{error_message} (Status Code: {status_code})" if status_code else error_message
    return {
        "success": False,
        "final_url": None,
        "data": {},
        "text": "",
        "text_length": 0,
        "message": msg
    }

if __name__ == "__main__":
    test_json_url = "https://api.github.com"
    print("=" * 70)
    print(f"Running JSON Ingestor self-test on: {test_json_url}")
    print("=" * 70)

    result = ingest_json(test_json_url)
    if result["success"]:
        print("\n SUCCESS!")
        print(f"Final URL:   {result['final_url']}")
        print(f"Text Length: {result['text_length']} chars")
        print("\nJSON Data Preview (Root Keys):")
        if isinstance(result["data"], dict):
            print(list(result["data"].keys()))
        elif isinstance(result["data"], list) and result["data"]:
            print(f"List of {len(result['data'])} elements. First element keys:")
            if isinstance(result["data"][0], dict):
                print(list(result["data"][0].keys()))
                
        print("\nIndented Text preview (first 300 chars):")
        print("-" * 50)
        print(result["text"][:300] + "\n...")
        print("-" * 50)
    else:
        print("\n FAILURE!")
        print(f"Message: {result['message']}")

    print("\n" + "=" * 70)
    print("Self-test completed!")
    print("=" * 70)
