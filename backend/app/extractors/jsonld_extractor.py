import json
from bs4 import BeautifulSoup

def extract_jsonld(html: str) -> list[dict]:
    """
    Locates script tags with type "application/ld+json".
    Safely deserializes the JSON objects.
    Handles single JSON objects as well as lists of JSON-LD schemas.
    Ignores malformed JSON strings without raising exceptions.
    
    Returns a list of deserialized dictionaries.
    """
    if not html or html.strip() == "":
        return []

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return []

    results = []
    
    # Find all <script type="application/ld+json"> tags
    scripts = soup.find_all("script", type="application/ld+json")
    
    for script in scripts:
        content = script.string
        if not content:
            continue
            
        content = content.strip()
        if not content:
            continue
            
        try:
            data = json.loads(content)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        results.append(item)
            elif isinstance(data, dict):
                results.append(data)
        except (json.JSONDecodeError, TypeError, ValueError):
            # Ignore malformed JSON-LD tags
            continue

    return results
