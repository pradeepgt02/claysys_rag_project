import sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright
from app import config

# Add the parent directory of this file to sys.path to support direct execution
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

def ingest_dynamic_page(url: str) -> dict:
    """
    Renders and extracts content from a dynamic JavaScript-rendered web page
    using a headless Playwright Chromium instance.
    - Viewport width 1440, height 900.
    - Custom User-Agent.
    - Enforces timeout from config.
    - Cleans body text (up to 100,000 characters).
    - Extracts absolute hyperlinks (up to 100).
    """
    playwright_context = None
    browser = None
    context = None
    page = None
    
    # Define realistic User-Agent
    user_agent = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    try:
        playwright_context = sync_playwright().start()
        # Launch Chromium in headless mode
        browser = playwright_context.chromium.launch(headless=True)
        # Create context with realistic viewport and user agent
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=user_agent
        )
        page = context.new_page()
        page.set_default_timeout(config.PLAYWRIGHT_TIMEOUT_MS)

        # Navigate to URL
        page.goto(url, wait_until="domcontentloaded")
        
        # Wait for network idle state (up to 10 seconds, ignore timeout)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
            
        # Extra wait of 1 second for animations or dynamic elements
        page.wait_for_timeout(1000)

        final_url = page.url
        title = page.title() or ""
        rendered_html = page.content() or ""
        
        # Extract visible body text
        raw_text = page.locator("body").inner_text() or ""
        lines = (line.strip() for line in raw_text.splitlines())
        non_empty_lines = [" ".join(line.split()) for line in lines if line]
        cleaned_text = "\n".join(non_empty_lines)
        
        # Cap text
        if len(cleaned_text) > 100000:
            cleaned_text = cleaned_text[:100000]

        # Extract headings in document order
        headings = []
        heading_elements = page.locator("h1, h2, h3")
        element_count = heading_elements.count()
        for i in range(element_count):
            h_text = heading_elements.nth(i).inner_text().strip()
            if h_text:
                headings.append(" ".join(h_text.split()))

        # Extract and format absolute links
        unique_links = []
        seen_links = set()
        
        # Evaluate anchor elements directly inside the browser environment for speed
        raw_links = page.locator("a[href]").evaluate_all(
            "elements => elements.map(e => ({ "
            "  href: e.getAttribute('href'), "
            "  innerText: e.innerText || '', "
            "  title: e.getAttribute('title') || '', "
            "  ariaLabel: e.getAttribute('aria-label') || '', "
            "  rel: e.getAttribute('rel') || '' "
            "}))"
        )
        for item in raw_links:
            href = item.get("href")
            if not href:
                continue
            href = href.strip()
            if not href or href.startswith("#"):
                continue
                
            lower_href = href.lower()
            if any(lower_href.startswith(prefix) for prefix in ("javascript:", "mailto:", "tel:", "data:")):
                continue
                
            absolute_url = urljoin(final_url, href)
            absolute_url_defrag = absolute_url.split('#')[0].strip()
            
            parsed_link = urlparse(absolute_url_defrag)
            if parsed_link.scheme not in ("http", "https"):
                continue
                
            if absolute_url_defrag not in seen_links:
                seen_links.add(absolute_url_defrag)
                
                link_obj = {
                    "url": absolute_url_defrag,
                    "anchor_text": item.get("innerText", "").strip(),
                    "title_attribute": item.get("title", "").strip(),
                    "aria_label": item.get("ariaLabel", "").strip(),
                    "rel": item.get("rel", "").strip(),
                    "source_page_url": final_url
                }
                unique_links.append(link_obj)
                if len(unique_links) >= 100:
                    break

        return {
            "success": True,
            "final_url": final_url,
            "title": title,
            "description": "",
            "headings": headings,
            "text": cleaned_text,
            "links": unique_links,
            "text_length": len(cleaned_text),
            "rendered_html": rendered_html,
            "content_type": "dynamic_html",
            "message": "Dynamic page rendered and extracted successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "final_url": url,
            "title": "",
            "description": "",
            "headings": [],
            "text": "",
            "links": [],
            "text_length": 0,
            "rendered_html": "",
            "content_type": "dynamic_html",
            "message": f"Playwright rendering failed: {str(e)}"
        }
    finally:
        # Safely shut down browser resources
        try:
            if page:
                page.close()
            if context:
                context.close()
            if browser:
                browser.close()
            if playwright_context:
                playwright_context.stop()
        except Exception:
            pass

if __name__ == "__main__":
    test_dynamic_url = "https://quotes.toscrape.com/js/"
    print("=" * 70)
    print(f"Running Dynamic Page Ingestor self-test on: {test_dynamic_url}")
    print("=" * 70)

    result = ingest_dynamic_page(test_dynamic_url)
    if result["success"]:
        print("\n SUCCESS!")
        print(f"Final URL:   {result['final_url']}")
        print(f"Title:       {result['title']}")
        print(f"Text Length: {result['text_length']} chars")
        
        print("\nHeadings:")
        print(result["headings"])
        
        print("\nRendered Text Preview (first 500 chars):")
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
