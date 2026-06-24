import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from requests.exceptions import Timeout, ConnectionError, SSLError, HTTPError
from app import config


def ingest_html(url: str) -> dict:
    """
    Downloads and extracts content from a static HTML website.
    - Sends a GET request with a 20-second timeout.
    - Strips scripts, styles, navigation, footers, forms, etc.
    - Extracts title, meta description, H1-H3 headings, text, and unique absolute hyperlinks.
    - Limits text output to 100,000 characters and links output to the first 100 links.
    """
    headers = {
        "User-Agent": "WebMind-RAG-Bot/1.0"
    }
    timeout = 20
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
    except Timeout:
        return create_failure_response("Connection timed out after 20 seconds.")
    except ConnectionError:
        return create_failure_response("Connection error: Server could not be reached.")
    except SSLError:
        return create_failure_response("SSL certificate verification failed.")
    except HTTPError as e:
        status = e.response.status_code if e.response is not None else None
        return create_failure_response(f"HTTP error occurred: {str(e)}", status_code=status)
    except Exception as e:
        return create_failure_response(f"An unexpected request error occurred: {str(e)}")

    final_url = response.url

    try:
        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        return create_failure_response(f"HTML parsing failed: {str(e)}")

    # 1. Strip unwanted elements
    unwanted_tags = ["script", "style", "noscript", "svg", "nav", "footer", "aside", "form", "iframe"]
    for tag in soup(unwanted_tags):
        tag.decompose()

    # 2. Extract Title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # 3. Extract Meta Description
    description = ""
    meta_desc = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "description"})
    if meta_desc and meta_desc.get("content"):
        description = meta_desc.get("content", "").strip()
    else:
        # Fallback to og:description if name="description" is missing
        og_desc = soup.find("meta", attrs={"property": lambda x: x and x.lower() == "og:description"})
        if og_desc and og_desc.get("content"):
            description = og_desc.get("content", "").strip()

    # 4. Extract Headings (h1, h2, h3)
    headings = []
    for heading_tag in soup.find_all(["h1", "h2", "h3"]):
        h_text = heading_tag.get_text().strip()
        if h_text:
            # Replace multiple spaces/newlines inside headings
            h_text_clean = " ".join(h_text.split())
            headings.append(h_text_clean)

    # 5. Extract and Clean Body Text
    try:
        raw_text = soup.get_text()
        lines = (line.strip() for line in raw_text.splitlines())
        # Clean inline duplicate spaces, keep non-empty lines
        non_empty_lines = [" ".join(line.split()) for line in lines if line]
        cleaned_text = "\n".join(non_empty_lines)
        
        # Safe character length limit
        if len(cleaned_text) > 100000:
            cleaned_text = cleaned_text[:100000]
    except Exception as e:
        cleaned_text = ""
        description = description or f"Warning: Text extraction encountered an issue: {str(e)}"

    # 6. Extract and Clean Hyperlinks
    unique_links = []
    seen_links = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if not href or href.startswith("#"):
            continue
            
        lower_href = href.lower()
        # Ignore non-http schemes (including data:)
        if any(lower_href.startswith(prefix) for prefix in ("javascript:", "mailto:", "tel:", "data:")):
            continue
            
        # Make the URL absolute using final_url context
        absolute_url = urljoin(final_url, href)
        
        # Remove fragment component
        absolute_url_defrag = absolute_url.split("#")[0].strip()
        if not absolute_url_defrag:
            continue
        
        # Validate absolute link scheme
        parsed_link = urlparse(absolute_url_defrag)
        if parsed_link.scheme not in ("http", "https"):
            continue
            
        if absolute_url_defrag not in seen_links:
            seen_links.add(absolute_url_defrag)
            
            # Extract metadata attributes safely joining lists if bs4 returns list types
            anchor_text = a_tag.get_text().strip()
            
            title_attr = a_tag.get("title", "")
            if isinstance(title_attr, list):
                title_attr = " ".join(title_attr)
            title_attr = title_attr.strip()
            
            aria_label = a_tag.get("aria-label", "")
            if isinstance(aria_label, list):
                aria_label = " ".join(aria_label)
            aria_label = aria_label.strip()
            
            rel_attr = a_tag.get("rel", "")
            if isinstance(rel_attr, list):
                rel_attr = " ".join(rel_attr)
            rel_attr = rel_attr.strip()
            
            link_obj = {
                "url": absolute_url_defrag,
                "anchor_text": anchor_text,
                "title_attribute": title_attr,
                "aria_label": aria_label,
                "rel": rel_attr,
                "source_page_url": final_url
            }
            unique_links.append(link_obj)
            # Cap links at 100 for safety
            if len(unique_links) >= 100:
                break

    text_length = len(cleaned_text)

    # 7. Check if fallback to Playwright is required for dynamic page content
    if text_length < config.DYNAMIC_PAGE_TEXT_THRESHOLD:
        # Dynamic JavaScript fallback
        from app.ingestion.dynamic_page_ingestor import ingest_dynamic_page
        playwright_res = ingest_dynamic_page(final_url)
        if playwright_res["success"]:
            playwright_res["rendering_method"] = "playwright"
            return playwright_res
        else:
            # If Playwright fails, return the original static content with a descriptive message
            return {
                "success": True,
                "final_url": final_url,
                "title": title,
                "description": description,
                "headings": headings,
                "text": cleaned_text,
                "links": unique_links,
                "text_length": text_length,
                "rendering_method": "static",
                "message": f"HTML content extracted statically (Playwright dynamic fallback failed: {playwright_res['message']})"
            }

    return {
        "success": True,
        "final_url": final_url,
        "title": title,
        "description": description,
        "headings": headings,
        "text": cleaned_text,
        "links": unique_links,
        "text_length": text_length,
        "rendering_method": "static",
        "message": "HTML content extracted successfully"
    }

def create_failure_response(error_message: str, status_code: int = None) -> dict:
    """Helper to structure failure dictionaries consistently."""
    return {
        "success": False,
        "final_url": None,
        "title": "",
        "description": "",
        "headings": [],
        "text": "",
        "links": [],
        "text_length": 0,
        "rendering_method": "static",
        "message": error_message
    }


if __name__ == "__main__":
    test_url = "https://www.python.org"
    print("=" * 70)
    print(f"Running HTML Ingestor self-test on: {test_url}")
    print("=" * 70)

    result = ingest_html(test_url)
    if result["success"]:
        print("\n SUCCESS!")
        print(f"Final URL:        {result['final_url']}")
        print(f"Title:            {result['title']}")
        print(f"Meta Description: {result['description']}")
        print(f"Text Length:      {result['text_length']} characters")
        print("\nHeadings (First 5):")
        for heading in result["headings"][:5]:
            print(f"  - {heading}")
        
        print("\nVisible Text Preview (First 500 chars):")
        print("-" * 50)
        print(result["text"][:500] + "\n...")
        print("-" * 50)

        print(f"\nLinks Extracted (Total {len(result['links'])}, showing first 10):")
        for link in result["links"][:10]:
            print(f"  - {link}")
    else:
        print("\n FAILURE!")
        print(f"Message: {result['message']}")

    print("\n" + "=" * 70)
    print("Self-test completed!")
    print("=" * 70)
