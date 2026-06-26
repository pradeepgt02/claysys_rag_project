import sys
from pathlib import Path

# Add the parent directory of this file to sys.path to support direct execution
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from urllib.parse import urlparse
from app.ingestion.url_validator import validate_url
from app.ingestion.html_ingestor import ingest_html
from app.crawler.url_normalizer import normalize_crawl_url
from app.crawler.crawl_queue import CrawlQueue
from app.crawler.link_discovery import discover_same_domain_links
from app.crawler.relevance_scorer import score_link_relevance

def crawl_website(start_url: str, max_pages: int = 5, initial_question: str = "") -> dict:
    """
    Crawls a website starting at start_url:
    - Validates and normalizes the start URL.
    - Limits crawling strictly to pages on the same domain or subdomains.
    - Respects the max_pages limit.
    - Gracefully continues if individual page ingestion fails.
    - Prioritizes crawling queue based on relevance score against initial_question.
    - Returns a structured dictionary containing success status, list of crawled pages, 
      visited URLs, and failed URLs.
    """
    # 1. Validate the start URL
    validation = validate_url(start_url)
    if not validation["valid"]:
        return {
            "success": False,
            "start_url": start_url,
            "pages_crawled": 0,
            "pages": [],
            "visited_urls": [],
            "failed_urls": [start_url],
            "message": f"Start URL validation failed: {validation['message']}"
        }

    # Normalize start URL consistently
    normalized_start_url = normalize_crawl_url(validation["normalized_url"])

    # 2. Extract base domain
    parsed_start = urlparse(normalized_start_url)
    base_domain = parsed_start.hostname
    if not base_domain:
        return {
            "success": False,
            "start_url": normalized_start_url,
            "pages_crawled": 0,
            "pages": [],
            "visited_urls": [],
            "failed_urls": [normalized_start_url],
            "message": "Could not determine the base domain from the start URL."
        }

    # Initialize queue and state variables
    queue = CrawlQueue()
    queue.add(normalized_start_url)

    visited_urls = set()
    failed_urls = set()
    pages = []

    # Relevance state tracking dictionaries
    url_relevance = {}
    url_reasons = {}
    url_matched_terms = {}

    # Score starting URL
    start_scoring = score_link_relevance(
        url=normalized_start_url,
        initial_question=initial_question
    )
    url_relevance[normalized_start_url] = start_scoring["score"]
    url_reasons[normalized_start_url] = start_scoring["reason"]
    url_matched_terms[normalized_start_url] = start_scoring["matched_terms"]

    # 3. Crawler Loop
    from concurrent.futures import ThreadPoolExecutor

    MAX_CONCURRENT_REQUESTS = 5

    while not queue.is_empty() and len(pages) < max_pages:
        batch_urls = []
        # Pop a batch of URLs
        while not queue.is_empty() and len(batch_urls) < MAX_CONCURRENT_REQUESTS and len(pages) + len(batch_urls) < max_pages:
            current_url = queue.pop()
            if current_url not in visited_urls and current_url not in failed_urls:
                batch_urls.append(current_url)
                # Optimistically mark as visited so we don't pick it up again if it appears multiple times
                visited_urls.add(current_url)

        if not batch_urls:
            continue

        # Ingest HTML contents concurrently
        with ThreadPoolExecutor(max_workers=len(batch_urls)) as executor:
            results = list(executor.map(ingest_html, batch_urls))

        # Process results
        for current_url, ingest_result in zip(batch_urls, results):
            if not ingest_result["success"]:
                # Track failed URL
                failed_urls.add(current_url)
                continue

            # Store parsed page contents (use normalized final_url)
            normalized_final_url = normalize_crawl_url(ingest_result["final_url"])
            
            # Ensure redirect URL has metadata
            if normalized_final_url not in url_relevance:
                url_relevance[normalized_final_url] = url_relevance.get(current_url, 0.0)
                url_reasons[normalized_final_url] = url_reasons.get(current_url, "")
                url_matched_terms[normalized_final_url] = url_matched_terms.get(current_url, [])

            pages.append({
                "url": normalized_final_url,
                "title": ingest_result["title"],
                "description": ingest_result["description"],
                "headings": ingest_result["headings"],
                "text": ingest_result["text"],
                "links": ingest_result["links"],
                "text_length": ingest_result["text_length"],
                "crawl_relevance_score": url_relevance.get(normalized_final_url, 0.0),
                "crawl_reason": url_reasons.get(normalized_final_url, ""),
                "matched_terms": url_matched_terms.get(normalized_final_url, [])
            })

            # We may have reached the limit if many redirects went to same page etc, though we limit batch based on max_pages
            if len(pages) >= max_pages:
                break

            # 4. Discover Same-Domain links from the current page
            discovered_links = discover_same_domain_links(
                page_url=ingest_result["final_url"],
                links=ingest_result["links"],
                base_domain=base_domain,
                initial_question=initial_question,
                page_title=ingest_result["title"]
            )

            # Add unique links to the crawl queue after normalizing and tracking their relevance
            for link in discovered_links:
                normalized_link = link["url"]
                
                # Keep highest score if link is discovered multiple times
                if normalized_link not in url_relevance or link["relevance_score"] > url_relevance[normalized_link]:
                    url_relevance[normalized_link] = link["relevance_score"]
                    url_reasons[normalized_link] = link["relevance_reason"]
                    url_matched_terms[normalized_link] = link["matched_terms"]

                if normalized_link not in visited_urls and normalized_link not in failed_urls:
                    queue.add(normalized_link)

        # Sort the CrawlQueue globally by relevance score descending on each discovery iteration
        from collections import deque
        queue._queue = deque(sorted(
            queue._queue,
            key=lambda u: (-url_relevance.get(u, 0.0), len(u))
        ))

    return {
        "success": True,
        "start_url": normalized_start_url,
        "pages_crawled": len(pages),
        "pages": pages,
        "visited_urls": list(visited_urls),
        "failed_urls": list(failed_urls),
        "message": f"Website crawl completed successfully. Crawled {len(pages)} page(s)."
    }


if __name__ == "__main__":
    import unittest.mock as mock

    # Mock database for Tests A, B, and C
    mock_pages = {
        "https://www.python.org/": {
            "success": True,
            "final_url": "https://www.python.org/",
            "title": "Welcome to Python.org",
            "description": "Python homepage",
            "headings": ["Python", "Downloads", "News"],
            "text": "This is python home page. We have programming resources.",
            "text_length": 54,
            "links": [
                {
                    "url": "https://www.python.org/downloads/",
                    "anchor_text": "Download Python",
                    "title_attribute": "Download installers",
                    "aria_label": "",
                    "rel": "",
                    "source_page_url": "https://www.python.org/"
                },
                {
                    "url": "https://www.python.org/privacy/",
                    "anchor_text": "Privacy Policy",
                    "title_attribute": "",
                    "aria_label": "",
                    "rel": "",
                    "source_page_url": "https://www.python.org/"
                },
                {
                    "url": "https://www.python.org/community/",
                    "anchor_text": "Community Page",
                    "title_attribute": "",
                    "aria_label": "",
                    "rel": "",
                    "source_page_url": "https://www.python.org/"
                },
                {
                    "url": "https://www.python.org/doc/",
                    "anchor_text": "Documentation and Tutorials",
                    "title_attribute": "Guides",
                    "aria_label": "",
                    "rel": "",
                    "source_page_url": "https://www.python.org/"
                },
                {
                    "url": "https://www.python.org/social/",
                    "anchor_text": "Twitter Account",
                    "title_attribute": "",
                    "aria_label": "",
                    "rel": "",
                    "source_page_url": "https://www.python.org/"
                }
            ]
        },
        "https://www.python.org/downloads/": {
            "success": True,
            "final_url": "https://www.python.org/downloads/",
            "title": "Download Python",
            "description": "Download page",
            "headings": ["Download", "Releases"],
            "text": "Here you can download python installers.",
            "text_length": 40,
            "links": []
        },
        "https://www.python.org/privacy/": {
            "success": True,
            "final_url": "https://www.python.org/privacy/",
            "title": "Privacy Policy",
            "description": "Privacy policy details",
            "headings": ["Privacy"],
            "text": "Privacy is important to us.",
            "text_length": 27,
            "links": []
        },
        "https://www.python.org/community/": {
            "success": True,
            "final_url": "https://www.python.org/community/",
            "title": "Community",
            "description": "Python community",
            "headings": ["Community"],
            "text": "Connect with python users.",
            "text_length": 26,
            "links": []
        },
        "https://www.python.org/doc/": {
            "success": True,
            "final_url": "https://www.python.org/doc/",
            "title": "Python Documentation",
            "description": "Docs and tutorials",
            "headings": ["Docs"],
            "text": "Learn python here.",
            "text_length": 18,
            "links": []
        },
        "https://www.python.org/social/": {
            "success": True,
            "final_url": "https://www.python.org/social/",
            "title": "Social",
            "description": "Social links",
            "headings": ["Social"],
            "text": "Twitter facebook details.",
            "text_length": 25,
            "links": []
        },
        "https://mystore.com/": {
            "success": True,
            "final_url": "https://mystore.com/",
            "title": "My Store",
            "description": "E-commerce store",
            "headings": ["Store", "Catalog"],
            "text": "Welcome to my online store.",
            "text_length": 27,
            "links": [
                {
                    "url": "https://mystore.com/products/shoes",
                    "anchor_text": "Buy Shoes - Product Catalog",
                    "title_attribute": "Shop shoes",
                    "aria_label": "",
                    "rel": "",
                    "source_page_url": "https://mystore.com/"
                },
                {
                    "url": "https://mystore.com/privacy-policy",
                    "anchor_text": "Privacy details",
                    "title_attribute": "",
                    "aria_label": "",
                    "rel": "",
                    "source_page_url": "https://mystore.com/"
                },
                {
                    "url": "https://mystore.com/about-us",
                    "anchor_text": "About our team",
                    "title_attribute": "",
                    "aria_label": "",
                    "rel": "",
                    "source_page_url": "https://mystore.com/"
                },
                {
                    "url": "https://mystore.com/contact-support",
                    "anchor_text": "Customer Help Support",
                    "title_attribute": "",
                    "aria_label": "",
                    "rel": "",
                    "source_page_url": "https://mystore.com/"
                }
            ]
        },
        "https://mystore.com/products/shoes": {
            "success": True,
            "final_url": "https://mystore.com/products/shoes",
            "title": "Buy Shoes",
            "description": "Shoe collection",
            "headings": ["Shoes"],
            "text": "Great shoes for sale.",
            "text_length": 21,
            "links": []
        },
        "https://mystore.com/privacy-policy": {
            "success": True,
            "final_url": "https://mystore.com/privacy-policy",
            "title": "Privacy",
            "description": "Privacy policy",
            "headings": ["Privacy"],
            "text": "Privacy terms.",
            "text_length": 14,
            "links": []
        },
        "https://mystore.com/about-us": {
            "success": True,
            "final_url": "https://mystore.com/about-us",
            "title": "About Us",
            "description": "About company",
            "headings": ["About"],
            "text": "We are a great team.",
            "text_length": 20,
            "links": []
        },
        "https://mystore.com/contact-support": {
            "success": True,
            "final_url": "https://mystore.com/contact-support",
            "title": "Contact Support",
            "description": "Support help",
            "headings": ["Support"],
            "text": "Help desk.",
            "text_length": 10,
            "links": []
        }
    }

    def mock_ingest_html(url):
        normalized = normalize_crawl_url(url)
        return mock_pages.get(normalized, {
            "success": False,
            "final_url": url,
            "title": "",
            "description": "",
            "headings": [],
            "text": "",
            "links": [],
            "text_length": 0,
            "rendering_method": "static",
            "message": "URL not in mock database"
        })

    def mock_validate_url(url):
        from app.ingestion.url_validator import normalize_url
        if "mystore.com" in url or "python.org" in url:
            return {
                "valid": True,
                "normalized_url": normalize_url(url),
                "message": "Valid URL (Mocked)"
            }
        from app.ingestion.url_validator import validate_url as real_validate_url
        return real_validate_url(url)

    with mock.patch("app.crawler.generic_crawler.ingest_html", side_effect=mock_ingest_html), \
         mock.patch("app.crawler.generic_crawler.validate_url", side_effect=mock_validate_url):

        print("=" * 70)
        print("Running Crawler Question-Aware Priority Self-Tests")
        print("=" * 70)

        # ----------------------------------------------------
        # Test A: Download python
        # ----------------------------------------------------
        q_a = "how to download python"
        print(f"\n[Test A] Crawling python.org for question: '{q_a}' (max_pages=2)")
        res_a = crawl_website("https://www.python.org", max_pages=2, initial_question=q_a)
        
        assert res_a["success"], "Test A failed execution"
        assert res_a["pages_crawled"] == 2, "Test A did not crawl 2 pages"
        p2_a = res_a["pages"][1]
        print(f"  First Crawled URL:  {res_a['pages'][0]['url']}")
        print(f"  Second Crawled URL: {p2_a['url']}")
        print(f"  Relevance Score:    {p2_a['crawl_relevance_score']}")
        print(f"  Reason:             {p2_a['crawl_reason']}")
        print(f"  Matched Terms:      {p2_a['matched_terms']}")
        
        assert "downloads" in p2_a["url"], "Test A did not prioritize downloads page"

        # ----------------------------------------------------
        # Test B: Python tutorial
        # ----------------------------------------------------
        q_b = "python tutorial for beginners"
        print(f"\n[Test B] Crawling python.org for question: '{q_b}' (max_pages=2)")
        res_b = crawl_website("https://www.python.org", max_pages=2, initial_question=q_b)
        
        assert res_b["success"], "Test B failed execution"
        assert res_b["pages_crawled"] == 2, "Test B did not crawl 2 pages"
        p2_b = res_b["pages"][1]
        print(f"  First Crawled URL:  {res_b['pages'][0]['url']}")
        print(f"  Second Crawled URL: {p2_b['url']}")
        print(f"  Relevance Score:    {p2_b['crawl_relevance_score']}")
        print(f"  Reason:             {p2_b['crawl_reason']}")
        print(f"  Matched Terms:      {p2_b['matched_terms']}")
        
        test_b_url = p2_b["url"].lower()

        assert any(keyword in test_b_url for keyword in [
            "doc",
            "tutorial",
            "gettingstarted",
            "getting-started",
            "guide",
            "learn",
            "reference",
        ]), "Test B did not prioritize a documentation/tutorial/getting-started page"

        # ----------------------------------------------------
        # Test C: Local Relevance Scoring Demo (no HTTP requests)
        # ----------------------------------------------------
        q_c = "I need a black ball pen under 500"
        print(f"\n[Test C] Local relevance scoring demo for question: '{q_c}'")

        sample_links = [
            {"url": "https://mystore.com/products/blue-pen",       "anchor_text": "Blue Pen"},
            {"url": "https://mystore.com/products/black-ball-pen", "anchor_text": "Black Ball Pen"},
            {"url": "https://mystore.com/collections/pens",        "anchor_text": "Shop Pens"},
            {"url": "https://mystore.com/pricing",                 "anchor_text": "Pricing"},
            {"url": "https://mystore.com/privacy",                 "anchor_text": "Privacy Policy"},
            {"url": "https://mystore.com/login",                   "anchor_text": "Login"},
        ]

        ranked_results = discover_same_domain_links(
            page_url="https://mystore.com/",
            links=sample_links,
            base_domain="mystore.com",
            initial_question=q_c,
            page_title="MyStore Online Shopping"
        )

        print(f"\n  {'Rank':<5} {'URL':<50} {'Score':<7} {'Matched':<30} Reason")
        print(f"  {'-'*4} {'-'*49} {'-'*6} {'-'*29} {'-'*30}")
        for rank, link in enumerate(ranked_results, start=1):
            print(
                f"  {rank:<5} {link['url']:<50} "
                f"{link['relevance_score']:<7.3f} "
                f"{str(link['matched_terms']):<30} "
                f"{link['relevance_reason']}"
            )

        black_ball_pen = normalize_crawl_url("https://mystore.com/products/black-ball-pen")
        collections_pens = normalize_crawl_url("https://mystore.com/collections/pens")
        pricing = normalize_crawl_url("https://mystore.com/pricing")
        privacy = normalize_crawl_url("https://mystore.com/privacy")
        login = normalize_crawl_url("https://mystore.com/login")

        scores = {
            normalize_crawl_url(item["url"]): item["relevance_score"]
            for item in ranked_results
        }

        required_urls = [
            black_ball_pen,
            collections_pens,
            pricing,
            privacy,
            login,
        ]

        for required_url in required_urls:
            assert required_url in scores, f"Expected URL missing from local scoring results: {required_url}"

        assert scores[black_ball_pen] > scores[pricing]
        assert scores[black_ball_pen] > scores[privacy]
        assert scores[black_ball_pen] > scores[login]
        assert scores[collections_pens] > scores[privacy]
        assert scores[collections_pens] > scores[login]

        print("All crawler relevance self-tests passed successfully.")
