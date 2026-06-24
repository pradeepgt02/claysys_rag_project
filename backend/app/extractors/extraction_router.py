import requests
import json
import copy
from bs4 import BeautifulSoup

from app.extractors.metadata_extractor import extract_metadata
from app.extractors.article_extractor import extract_article_content
from app.extractors.documentation_extractor import extract_documentation_sections
from app.extractors.table_extractor import extract_tables
from app.extractors.jsonld_extractor import extract_jsonld
from app.extractors.product_extractor import extract_product_data
from app.extractors.content_cleaner import clean_text

def _extract_full_body_text(html: str) -> str:
    """
    Extracts text from the HTML body, removing script/style tags and layout elements,
    and returns a cleaned version of the text as a fallback.
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        body = soup.find("body") or soup
        
        # Clone the body element to avoid modifying the original soup
        body_copy = copy.copy(body)
        
        unwanted_tags = ["script", "style", "noscript", "nav", "footer", "aside", "form", "iframe", "svg", "header"]
        for tag in body_copy(unwanted_tags):
            tag.decompose()
            
        raw_text = body_copy.get_text()
        return clean_text(raw_text)
    except Exception:
        return ""

def extract_structured_content(html: str) -> dict:
    """
    Aggregates all content extractors to form a single cohesive page analysis result.
    If the extracted main article text is too short (< 200 characters),
    falls back to using the cleaned full body text.
    
    Returns a dictionary of structured data:
    {
      "metadata": {...},
      "article": {...},
      "documentation_sections": [...],
      "tables": [...],
      "jsonld": [...],
      "products": [...],
      "clean_text": "..."
    }
    """
    if not html or html.strip() == "":
        return {
            "metadata": {},
            "article": {},
            "documentation_sections": [],
            "tables": [],
            "jsonld": [],
            "products": [],
            "clean_text": ""
        }

    # Execute all sub-extractors
    metadata = extract_metadata(html)
    article = extract_article_content(html)
    documentation_sections = extract_documentation_sections(html)
    tables = extract_tables(html)
    jsonld = extract_jsonld(html)
    products = extract_product_data(jsonld)

    # Clean the article text
    article_text = article.get("text", "")
    cleaned_article_text = clean_text(article_text)

    # Determine if we need to fall back to full body text
    if len(cleaned_article_text) < 200:
        clean_text_result = _extract_full_body_text(html)
    else:
        clean_text_result = cleaned_article_text

    return {
        "metadata": metadata,
        "article": article,
        "documentation_sections": documentation_sections,
        "tables": tables,
        "jsonld": jsonld,
        "products": products,
        "clean_text": clean_text_result
    }

if __name__ == "__main__":
    print("=" * 60)
    print("Running Self-Test on Extraction Router...")
    print("=" * 60)
    
    target_url = "https://fastapi.tiangolo.com/"
    print(f"Downloading: {target_url}")
    
    try:
        response = requests.get(
            target_url,
            headers={"User-Agent": "WebMind-RAG-Bot/1.0"},
            timeout=15,
            allow_redirects=True
        )
        response.raise_for_status()
        html_content = response.text
        print(f"Downloaded successfully. HTML length: {len(html_content)} characters.")
        
        # Parse content
        extracted = extract_structured_content(html_content)
        
        print("\n--- RESULTS HIGHLIGHTS ---")
        print(f"Title: {extracted['metadata'].get('title')}")
        print(f"Language: {extracted['metadata'].get('language')}")
        print(f"Article Text Length: {extracted['article'].get('text_length')}")
        print(f"Headings Count: {len(extracted['article'].get('headings', []))}")
        print(f"Documentation Sections Count: {len(extracted['documentation_sections'])}")
        print(f"Tables Found: {len(extracted['tables'])}")
        print(f"JSON-LD Schemas Found: {len(extracted['jsonld'])}")
        print(f"Products Found: {len(extracted['products'])}")
        print(f"Final Clean Text Length: {len(extracted['clean_text'])}")
        
        if extracted['article'].get('headings'):
            print("\nFirst 5 Headings:")
            for h in extracted['article']['headings'][:5]:
                print(f" - {h}")
                
        if extracted['clean_text']:
            print("\nClean Text Snippet (First 500 characters):")
            print("-" * 50)
            print(extracted['clean_text'][:500] + "...")
            print("-" * 50)
            
    except Exception as e:
        print(f"Error during self-test: {e}")
