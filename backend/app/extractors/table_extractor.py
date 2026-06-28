from bs4 import BeautifulSoup

def clean_cell_text(text: str) -> str:
    """
    Cleans cell text by stripping whitespace, replacing pipe characters to prevent
    markdown breakage, and collapsing sequential spaces/newlines.
    """
    if not text:
        return ""
    # Escape pipe characters and normalize spacing
    return " ".join(text.replace("|", "\\|").split()).strip()

def extract_tables(html: str) -> list[dict]:
    """
    Locates <table> elements.
    Extracts table headers (<th>) and rows (<td>).
    Formats table structure to a readable Markdown-like tabular text snippet.
    
    Implements safety limits:
    - Maximum 10 tables parsed.
    - Maximum 100 rows parsed per table.
    
    Returns a list of dicts:
    [
      {
        "headers": [col1, col2, ...],
        "rows": [[val1, val2, ...], ...],
        "text": "tabular formatting string"
      }
    ]
    """
    if not html or html.strip() == "":
        return []

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return []

    # Find all table elements
    tables = soup.find_all("table")
    if not tables:
        return []

    results = []

    for table in tables[:10]:
        headers = []
        rows = []

        # Find rows in the table
        tr_elements = table.find_all("tr")
        if not tr_elements:
            continue

        for tr in tr_elements[:100]:
            # Look for th and td elements inside the row
            cells = tr.find_all(["th", "td"])
            if not cells:
                continue

            # Determine if this row is primarily headers
            is_header_row = all(c.name == "th" for c in cells)

            cell_texts = [clean_cell_text(c.get_text()) for c in cells]

            if is_header_row and not headers:
                headers = cell_texts
            else:
                rows.append(cell_texts)

        # If headers are empty but we have rows, check if we want to use the first row as header
        # but let's keep headers empty if no explicit th tags were matched as header row.
        
        # Build markdown-like table text
        markdown_lines = []
        if headers:
            markdown_lines.append("| " + " | ".join(headers) + " |")
            markdown_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        for row in rows:
            markdown_lines.append("| " + " | ".join(row) + " |")

        table_text = "\n".join(markdown_lines)

        results.append({
            "headers": headers,
            "rows": rows,
            "text": table_text
        })

    return results
