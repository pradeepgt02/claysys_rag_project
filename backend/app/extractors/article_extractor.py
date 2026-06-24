from bs4 import BeautifulSoup

def extract_article_content(html: str) -> dict:
    """
    Identifies and extracts the main article/body content from HTML markup:
    - Prioritizes article, main, [role="main"], common container identifiers, and falls back to body.
    - Strips scripts, navigation, footers, forms, cookies, and social widgets.
    - Returns structured text content, headings, and paragraph details.
    """
    empty_result = {
        "text": "",
        "headings": [],
        "paragraph_count": 0,
        "text_length": 0
    }

    if not html or html.strip() == "":
        return empty_result

    try:
        # Load the HTML document
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return empty_result

    # 1. Locate the main content container in order of semantic priority
    main_el = soup.find("article")

    if not main_el:
        main_el = soup.find("main")

    if not main_el:
        main_el = soup.find(attrs={"role": "main"})

    # Check common class or id values
    common_targets = ["content", "article", "post", "entry", "documentation"]
    if not main_el:
        for keyword in common_targets:
            # Check ID matches
            main_el = soup.find(id=lambda val: val and keyword in val.lower())
            if main_el:
                break
            # Check Class matches
            main_el = soup.find(class_=lambda val: val and (
                any(keyword in c.lower() for c in val) if isinstance(val, list) else keyword in val.lower()
            ))
            if main_el:
                break

    # Fallback to body or entire soup if no main selector matched
    if not main_el:
        main_el = soup.find("body")
    if not main_el:
        main_el = soup

    # Make a copy of the elements subtree so we don't destroy the original soup tree structure
    import copy
    main_el = copy.copy(main_el)

    # 2. Prune unwanted tags
    unwanted_tags = ["script", "style", "noscript", "nav", "footer", "aside", "form", "iframe", "svg", "header"]
    for tag in main_el(unwanted_tags):
        tag.decompose()

    # 3. Prune class/id-based widgets (social, ads, popups)
    garbage_keywords = ["cookie", "privacy", "consent", "banner-ad", "social-share", "share-buttons", "widget-share"]
    
    for tag in main_el.find_all(lambda t: t.name in ("div", "section", "aside", "p", "span")):
        tag_id = tag.get("id", "") or ""
        tag_classes = tag.get("class", [])
        tag_class_str = " ".join(tag_classes) if isinstance(tag_classes, list) else str(tag_classes or "")
        
        # Check if ID or class matches any garbage keywords
        if any(kw in tag_id.lower() or kw in tag_class_str.lower() for kw in garbage_keywords):
            tag.decompose()

    # 4. Extract semantic text elements
    headings = []
    for heading in main_el.find_all(["h1", "h2", "h3"]):
        h_text = heading.get_text().strip()
        if h_text:
            headings.append(" ".join(h_text.split()))

    paragraph_count = len(main_el.find_all("p"))

    # Extract cleaned visible text
    raw_text = main_el.get_text()
    lines = (line.strip() for line in raw_text.splitlines())
    non_empty_lines = [" ".join(line.split()) for line in lines if line]
    cleaned_text = "\n".join(non_empty_lines)

    return {
        "text": cleaned_text,
        "headings": headings,
        "paragraph_count": paragraph_count,
        "text_length": len(cleaned_text)
    }
