import requests
from requests.exceptions import Timeout, ConnectionError, SSLError, TooManyRedirects, HTTPError

def detect_content_type(url: str) -> dict:
    """
    Detects the content type of a remote URL.
    - Sends a lightweight HEAD request first.
    - Falls back to a GET request with stream=True if HEAD fails or doesn't return a Content-Type.
    - Uses a 15-second timeout and custom User-Agent.
    - Standardizes the output to 'html', 'pdf', 'json', 'text', or 'unsupported'.
    """
    headers = {
        "User-Agent": "WebMind-RAG-Bot/1.0"
    }
    timeout = 15
    response = None

    # Step 1: Attempt a HEAD request (lightweight)
    try:
        response = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
    except Exception:
        # If HEAD fails or is rejected, we fallback to GET (stream=True)
        response = None

    # Step 2: Fallback to GET with stream=True if HEAD didn't work or had no Content-Type
    if response is None or not response.headers.get("Content-Type"):
        try:
            response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
            response.raise_for_status()
        except Timeout:
            return {
                "success": False,
                "final_url": None,
                "status_code": None,
                "content_type": "unknown",
                "raw_content_type": None,
                "message": "Connection timed out after 15 seconds."
            }
        except ConnectionError:
            return {
                "success": False,
                "final_url": None,
                "status_code": None,
                "content_type": "unknown",
                "raw_content_type": None,
                "message": "Connection error occurred. Server could not be reached."
            }
        except SSLError:
            return {
                "success": False,
                "final_url": None,
                "status_code": None,
                "content_type": "unknown",
                "raw_content_type": None,
                "message": "SSL certificate verification failed."
            }
        except TooManyRedirects:
            return {
                "success": False,
                "final_url": None,
                "status_code": None,
                "content_type": "unknown",
                "raw_content_type": None,
                "message": "Too many redirects occurred while following the URL."
            }
        except HTTPError as e:
            return {
                "success": False,
                "final_url": url,
                "status_code": e.response.status_code if e.response is not None else None,
                "content_type": "unknown",
                "raw_content_type": None,
                "message": f"HTTP error occurred: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "final_url": None,
                "status_code": None,
                "content_type": "unknown",
                "raw_content_type": None,
                "message": f"An unexpected request error occurred: {str(e)}"
            }

    # Step 3: Process the successful response headers
    try:
        response.raise_for_status()
        final_url = response.url
        status_code = response.status_code
        raw_header = response.headers.get("Content-Type", "")

        if not raw_header:
            return {
                "success": False,
                "final_url": final_url,
                "status_code": status_code,
                "content_type": "unknown",
                "raw_content_type": None,
                "message": "No Content-Type header returned by the server."
            }

        # Parse type and subtype (e.g. "text/html; charset=utf-8" -> "text/html")
        raw_content_type = raw_header.split(";")[0].strip().lower()

        # Map to application-recognized short names
        if raw_content_type == "text/html":
            mapped_type = "html"
        elif raw_content_type == "application/pdf":
            mapped_type = "pdf"
        elif raw_content_type in ("application/json", "text/json"):
            mapped_type = "json"
        elif raw_content_type == "text/plain":
            mapped_type = "text"
        else:
            mapped_type = "unsupported"

        # Reject unsupported types
        if mapped_type == "unsupported":
            return {
                "success": False,
                "final_url": final_url,
                "status_code": status_code,
                "content_type": "unsupported",
                "raw_content_type": raw_header,
                "message": f"Unsupported content type: '{raw_header}'"
            }

        return {
            "success": True,
            "final_url": final_url,
            "status_code": status_code,
            "content_type": mapped_type,
            "raw_content_type": raw_header,
            "message": "Content type detected successfully"
        }

    except HTTPError as e:
        return {
            "success": False,
            "final_url": response.url,
            "status_code": response.status_code,
            "content_type": "unknown",
            "raw_content_type": response.headers.get("Content-Type"),
            "message": f"HTTP status error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "final_url": None,
            "status_code": None,
            "content_type": "unknown",
            "raw_content_type": None,
            "message": f"Error parsing response headers: {str(e)}"
        }
    finally:
        if response is not None:
            response.close()

if __name__ == "__main__":
    test_urls = [
        "https://www.python.org",
        "https://api.github.com",
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "https://httpstat.us/404"
    ]

    print("=" * 70)
    print("Running Content Type Detector self-tests...")
    print("=" * 70)

    for test_url in test_urls:
        print(f"\nTesting Connection: {test_url}")
        result = detect_content_type(test_url)
        if result["success"]:
            print(f"  SUCCESS!")
            print(f"  Final URL:    {result['final_url']}")
            print(f"  Status Code:  {result['status_code']}")
            print(f"  Mapped Type:  {result['content_type']}")
            print(f"  Raw Header:   {result['raw_content_type']}")
        else:
            print(f"  FAILED!")
            print(f"  Status Code:  {result['status_code']}")
            print(f"  Mapped Type:  {result['content_type']}")
            print(f"  Message:      {result['message']}")

    print("\n" + "=" * 70)
    print("Self-tests completed!")
    print("=" * 70)
