from app.crawler.url_normalizer import normalize_crawl_url, is_same_domain, is_crawlable_url
from app.crawler.relevance_scorer import score_link_relevance

def discover_same_domain_links(
    page_url: str,
    links: list,
    base_domain: str,
    initial_question: str = "",
    page_title: str = ""
) -> list[dict]:
    """
    Processes a list of links discovered on a page:
    - Accepts both strings and dictionary objects.
    - Normalizes each link.
    - Filters to keep only crawlable URLs belonging to the base domain/subdomain.
    - Runs score_link_relevance for each.
    - Sorts the results by relevance_score descending, and len(url) ascending on ties.
    - Returns up to 100 structured ranked link dicts.
    """
    discovered_links = []
    seen_links = set()

    for item in links:
        if not item:
            continue

        # Extract properties depending on type
        if isinstance(item, dict):
            url = item.get("url", "")
            anchor_text = item.get("anchor_text", "")
            title_attribute = item.get("title_attribute", "")
            aria_label = item.get("aria_label", "")
            rel = item.get("rel", "")
            source_page_url = item.get("source_page_url", page_url)
        else:
            url = str(item)
            anchor_text = ""
            title_attribute = ""
            aria_label = ""
            rel = ""
            source_page_url = page_url

        if not url:
            continue

        # Normalize the link URL
        normalized_url = normalize_crawl_url(url)
        if not normalized_url:
            continue

        # Check safety/crawlability and same-domain constraint
        if is_crawlable_url(normalized_url) and is_same_domain(normalized_url, base_domain):
            if normalized_url not in seen_links:
                seen_links.add(normalized_url)
                
                # Run scorer
                scoring_res = score_link_relevance(
                    url=normalized_url,
                    anchor_text=anchor_text,
                    title_attribute=title_attribute,
                    aria_label=aria_label,
                    page_title=page_title,
                    initial_question=initial_question
                )
                
                link_obj = {
                    "url": normalized_url,
                    "anchor_text": anchor_text,
                    "title_attribute": title_attribute,
                    "aria_label": aria_label,
                    "rel": rel,
                    "source_page_url": source_page_url,
                    "relevance_score": scoring_res["score"],
                    "relevance_reason": scoring_res["reason"],
                    "matched_terms": scoring_res["matched_terms"]
                }
                discovered_links.append(link_obj)

    # Sort results by relevance_score descending, and len(url) ascending (prefer shorter URLs on ties)
    discovered_links.sort(key=lambda x: (-x["relevance_score"], len(x["url"])))

    # Limit to top 100 links
    return discovered_links[:100]
