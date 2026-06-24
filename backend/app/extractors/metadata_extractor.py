from bs4 import BeautifulSoup

def extract_metadata(html: str) -> dict:
    """
    Extracts webpage metadata:
    - HTML title tag.
    - Meta description.
    - Canonical link URL.
    - Open Graph title, description, and image.
    - HTML language configuration tag.
    Returns clean string values for any missing attributes.
    """
    empty_result = {
        "title": "",
        "description": "",
        "canonical_url": "",
        "og_title": "",
        "og_description": "",
        "og_image": "",
        "language": ""
    }

    if not html or html.strip() == "":
        return empty_result

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return empty_result

    # 1. HTML Title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # 2. Meta description
    description = ""
    meta_desc = soup.find("meta", attrs={"name": lambda x: x and x.lower() == "description"})
    if meta_desc:
        description = meta_desc.get("content", "").strip()

    # 3. Canonical URL
    canonical_url = ""
    canonical = soup.find("link", rel=lambda x: x and x.lower() == "canonical")
    if canonical:
        canonical_url = canonical.get("href", "").strip()

    # 4. Open Graph details
    og_title = ""
    og_title_meta = soup.find("meta", property=lambda x: x and x.lower() == "og:title")
    if og_title_meta:
        og_title = og_title_meta.get("content", "").strip()

    og_description = ""
    og_desc_meta = soup.find("meta", property=lambda x: x and x.lower() == "og:description")
    if og_desc_meta:
        og_description = og_desc_meta.get("content", "").strip()

    og_image = ""
    og_image_meta = soup.find("meta", property=lambda x: x and x.lower() == "og:image")
    if og_image_meta:
        og_image = og_image_meta.get("content", "").strip()

    # 5. Language from <html> tag
    language = ""
    html_tag = soup.find("html")
    if html_tag:
        language = html_tag.get("lang", "").strip()

    # Cleanup text formatting (collapsing spaces)
    return {
        "title": " ".join(title.split()),
        "description": " ".join(description.split()),
        "canonical_url": canonical_url,
        "og_title": " ".join(og_title.split()),
        "og_description": " ".join(og_description.split()),
        "og_image": og_image,
        "language": " ".join(language.split())
    }
