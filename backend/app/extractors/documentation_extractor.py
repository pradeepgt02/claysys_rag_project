from bs4 import BeautifulSoup, NavigableString, Comment

def extract_documentation_sections(html: str) -> list[dict]:
    """
    Breaks page content into sections based on <h1>, <h2>, <h3> heading selectors.
    Text under each heading is accumulated until the next heading of equal or higher level is reached.
    
    Returns a list of dictionaries:
    [
        {"heading": heading_text, "level": heading_level, "text": section_text},
        ...
    ]
    Caps text under each section at 50,000 characters.
    """
    if not html or html.strip() == "":
        return []

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return []

    # Locate main body/content or fallback to entire document
    body = soup.find("body") or soup

    # Prune unwanted elements to avoid indexing footer/nav headers
    unwanted_tags = ["script", "style", "noscript", "nav", "footer", "aside", "form", "iframe", "svg", "header"]
    for tag in body(unwanted_tags):
        tag.decompose()

    # Find all h1, h2, h3 elements in document order
    headings = body.find_all(["h1", "h2", "h3"])
    if not headings:
        return []

    level_map = {"h1": 1, "h2": 2, "h3": 3}
    results = []

    for i, heading in enumerate(headings):
        heading_text = " ".join(heading.get_text().split()).strip()
        if not heading_text:
            continue

        heading_level = level_map[heading.name.lower()]

        # Find the next heading that has an equal or higher level (level <= heading_level)
        next_stop_heading = None
        for next_h in headings[i+1:]:
            next_h_level = level_map[next_h.name.lower()]
            if next_h_level <= heading_level:
                next_stop_heading = next_h
                break

        # Traverse document order after this heading and collect text nodes until next_stop_heading
        section_pieces = []
        curr = heading.next_element

        while curr and curr != next_stop_heading:
            if isinstance(curr, NavigableString):
                # Ensure the text node is not inside the current heading tag itself
                if not isinstance(curr, Comment) and heading not in curr.parents:
                    val = curr.string
                    if val:
                        section_pieces.append(val)
            elif curr.name in ["p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "td", "th"]:
                # Insert newline boundaries for block elements to preserve line breaks
                section_pieces.append("\n")
            curr = curr.next_element

        # Clean the accumulated text
        raw_section_text = "".join(section_pieces)
        lines = (line.strip() for line in raw_section_text.splitlines())
        non_empty_lines = [" ".join(line.split()) for line in lines if line]
        section_text = "\n".join(non_empty_lines)

        # Cap section text safely
        section_text = section_text[:50000]

        results.append({
            "heading": heading_text,
            "level": heading_level,
            "text": section_text
        })

    return results
