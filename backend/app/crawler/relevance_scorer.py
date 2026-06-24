import re
from urllib.parse import urlparse, parse_qsl

STOP_WORDS = {
    "how", "what", "where", "when", "why", "is", "are", "the", "a", "an", 
    "to", "for", "of", "in", "on", "with", "can", "i", "me", "my"
}

def _normalize_word(word: str) -> str:
    """
    Simple beginner-friendly word normalizer for plural/singular matching.
    - Lowercase
    - Remove punctuation
    - For words longer than 3 characters, strip a trailing 's' so that
      plurals like 'pens', 'products', 'downloads', 'tutorials', 'installers'
      match their singular question counterparts.
    No heavy NLP libraries are used.
    """
    # Lowercase and strip leading/trailing non-alpha characters
    w = re.sub(r'[^a-z]', '', word.lower())
    # Strip trailing 's' only for words longer than 3 characters
    if len(w) > 3 and w.endswith('s'):
        w = w[:-1]
    return w

def normalize_and_tokenize(text: str) -> list[str]:
    """
    Cleans, tokenizes, and removes stop words from input text.
    """
    if not text:
        return []
    # Replace punctuation with spaces
    text_clean = re.sub(r'[^\w\s\-]', ' ', text.lower())
    # Split by hyphens and underscores as well
    text_clean = text_clean.replace("-", " ").replace("_", " ")
    words = text_clean.split()
    return [w for w in words if w not in STOP_WORDS]

def has_any_match(words_list: list[str], text: str) -> bool:
    """Helper to check if any pattern word matches inside the lowercased text."""
    text_lower = text.lower()
    return any(w in text_lower for w in words_list)

def score_link_relevance(
    url: str,
    anchor_text: str = "",
    title_attribute: str = "",
    aria_label: str = "",
    page_title: str = "",
    initial_question: str = ""
) -> dict:
    """
    Scores the relevance of a URL link against a user's question or generic usefulness terms.
    """
    score = 0.0
    matched_terms = []
    reasons = []

    # Parse URL components
    try:
        parsed = urlparse(url)
        path_text = parsed.path
        query_params = parse_qsl(parsed.query)
        query_words = []
        for key, val in query_params:
            query_words.append(key)
            query_words.append(val)
        query_text = " ".join(query_words)
    except Exception:
        path_text = ""
        query_text = ""
        query_params = []
        parsed = None

    # A. Normalize and tokenize fields
    path_words = normalize_and_tokenize(path_text)
    query_words_tokenized = normalize_and_tokenize(query_text)
    anchor_words = normalize_and_tokenize(anchor_text)
    title_words = normalize_and_tokenize(title_attribute)
    aria_words = normalize_and_tokenize(aria_label)
    page_title_words = normalize_and_tokenize(page_title)

    # Combined text for intent matching and penalties
    path_lower = path_text.lower()
    anchor_lower = anchor_text.lower()
    combined_link_text = f"{path_lower} {anchor_lower} {title_attribute.lower()} {aria_label.lower()} {query_text.lower()}"

    # E. Reject media/resource files completely (Early exit)
    if parsed:
        reject_extensions = {
            ".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js", 
            ".woff", ".woff2", ".ttf", ".eot", ".mp4", ".mp3", ".webm", 
            ".zip", ".exe", ".apk", ".docx", ".xlsx", ".pptx", ".pdf", ".json"
        }
        parsed_path = parsed.path.lower()
        has_reject_ext = any(parsed_path.endswith(ext) for ext in reject_extensions)
        
        reject_keywords = ["/image", "/css", "/js", "/font", "/video", "/audio"]
        has_reject_keyword = any(kw in parsed_path for kw in reject_keywords)
        
        if has_reject_ext or has_reject_keyword:
            return {
                "score": -9999.0,
                "matched_terms": [],
                "reason": "Rejected: media/resource file type"
            }

    question_words = normalize_and_tokenize(initial_question)

    if question_words:
        # C. Question keyword matching
        question_lower = initial_question.lower()
        
        for word in set(question_words):
            word_matched = False
            word_score = 0.0

            # Normalized form of the question word for plural-tolerant matching
            norm_word = _normalize_word(word)

            # Normalize every candidate token for comparison; keep original word
            # in matched_terms so output stays human-readable.
            if any(norm_word == _normalize_word(w) for w in path_words) or \
               any(norm_word == _normalize_word(w) for w in query_words_tokenized):
                word_score += 4.0
                word_matched = True
                reasons.append(f"Matched '{word}' in URL (+4)")

            if any(norm_word == _normalize_word(w) for w in anchor_words):
                word_score += 3.0
                word_matched = True
                reasons.append(f"Matched '{word}' in anchor text (+3)")

            if any(norm_word == _normalize_word(w) for w in title_words) or \
               any(norm_word == _normalize_word(w) for w in aria_words):
                word_score += 2.0
                word_matched = True
                reasons.append(f"Matched '{word}' in metadata (+2)")

            if any(norm_word == _normalize_word(w) for w in page_title_words):
                word_score += 1.0
                word_matched = True
                reasons.append(f"Matched '{word}' in source page title (+1)")

            if word_matched:
                score += word_score
                matched_terms.append(word)

        # Extra +5 if 2+ question words appear in the same path or anchor text
        # Use normalized comparison so plurals still count toward co-occurrence.
        norm_path_words = [_normalize_word(w) for w in path_words]
        norm_anchor_words = [_normalize_word(w) for w in anchor_words]
        matched_in_path = [w for w in matched_terms if _normalize_word(w) in norm_path_words]
        matched_in_anchor = [w for w in matched_terms if _normalize_word(w) in norm_anchor_words]
        if len(matched_in_path) >= 2 or len(matched_in_anchor) >= 2:
            score += 5.0
            reasons.append("Multiple matching terms co-occurred (+5)")

        # D. Generic intent keyword boosts (+8)
        intent_boost = 8.0
        
        # 1. Download
        if any(w in question_lower for w in ["download", "install", "setup", "get"]):
            download_words = ["download", "downloads", "install", "installation", "setup", "getting-started", "get-started", "release", "releases", "windows", "macos", "linux", "package"]
            if has_any_match(download_words, combined_link_text):
                score += intent_boost
                reasons.append("Download/Install intent matched (+8)")
                
        # 2. Documentation
        if any(w in question_lower for w in ["documentation", "docs", "learn", "tutorial", "guide", "example"]):
            docs_words = ["docs", "documentation", "tutorial", "guide", "learn", "examples", "reference", "api", "quickstart", "getting-started"]
            if has_any_match(docs_words, combined_link_text):
                score += intent_boost
                reasons.append("Documentation/Tutorial intent matched (+8)")
                
        # 3. Pricing
        if any(w in question_lower for w in ["price", "pricing", "cost", "plan", "subscription"]):
            price_words = ["pricing", "price", "plans", "billing", "subscription", "purchase"]
            if has_any_match(price_words, combined_link_text):
                score += intent_boost
                reasons.append("Pricing intent matched (+8)")
                
        # 4. Product
        if any(w in question_lower for w in ["product", "buy", "shop", "order", "cart"]):
            product_words = ["products", "product", "shop", "store", "buy", "order", "cart", "category", "collection"]
            if has_any_match(product_words, combined_link_text):
                score += intent_boost
                reasons.append("Product/Shopping intent matched (+8)")
                
        # 5. Support
        if any(w in question_lower for w in ["contact", "support", "help", "issue"]):
            support_words = ["contact", "support", "help", "faq", "troubleshooting", "community", "forum"]
            if has_any_match(support_words, combined_link_text):
                score += intent_boost
                reasons.append("Support/Contact intent matched (+8)")
                
        # 6. Login
        if any(w in question_lower for w in ["login", "account", "profile"]):
            login_words = ["login", "sign-in", "account", "profile", "dashboard"]
            if has_any_match(login_words, combined_link_text):
                score += intent_boost
                reasons.append("Login/Account intent matched (+8)")
                
        # 7. Company
        if any(w in question_lower for w in ["company", "about", "team", "career"]):
            company_words = ["about", "company", "team", "careers", "jobs", "leadership", "mission"]
            if has_any_match(company_words, combined_link_text):
                score += intent_boost
                reasons.append("Company/About intent matched (+8)")

        # E. Low-value page penalties (only if question doesn't ask for them)
        if not any(w in question_lower for w in ["privacy", "terms", "cookies", "legal", "policy"]):
            privacy_words = ["privacy", "terms", "cookies", "legal", "policy"]
            if has_any_match(privacy_words, combined_link_text):
                score -= 12.0
                reasons.append("Privacy/Terms penalty (-12)")
                
        if not any(w in question_lower for w in ["login", "logout", "signup", "register"]):
            login_pen_words = ["login", "logout", "signup", "register"]
            if has_any_match(login_pen_words, combined_link_text):
                score -= 8.0
                reasons.append("Login/Register penalty (-8)")
                
        if not any(w in question_lower for w in ["social", "twitter", "facebook", "instagram", "linkedin", "youtube"]):
            social_words = ["twitter", "facebook", "instagram", "linkedin", "youtube", "social"]
            if has_any_match(social_words, combined_link_text):
                score -= 10.0
                reasons.append("Social media penalty (-10)")
                
        if not any(w in question_lower for w in ["share", "print", "rss", "feed"]):
            share_words = ["share", "print", "rss", "feed"]
            if has_any_match(share_words, combined_link_text):
                score -= 8.0
                reasons.append("Share/RSS penalty (-8)")

    else:
        # G. Generic content value (when initial_question is empty)
        generic_val_words = ["docs", "documentation", "guide", "tutorial", "learn", "product", "products", "pricing", "price", "about", "support", "blog", "article", "faq"]
        if has_any_match(generic_val_words, combined_link_text):
            score += 5.0
            reasons.append("Generic content match (+5)")
            
        # Apply standard low-value penalties under empty question fallback
        privacy_words = ["privacy", "terms", "cookies", "legal", "policy"]
        if has_any_match(privacy_words, combined_link_text):
            score -= 12.0
            reasons.append("Generic privacy/terms penalty (-12)")
            
        login_pen_words = ["login", "logout", "signup", "register"]
        if has_any_match(login_pen_words, combined_link_text):
            score -= 8.0
            reasons.append("Generic login penalty (-8)")
            
        social_words = ["twitter", "facebook", "instagram", "linkedin", "youtube", "social"]
        if has_any_match(social_words, combined_link_text):
            score -= 10.0
            reasons.append("Generic social media penalty (-10)")
            
        share_words = ["share", "print", "rss", "feed"]
        if has_any_match(share_words, combined_link_text):
            score -= 8.0
            reasons.append("Generic share/RSS penalty (-8)")

    # E/G. Language switchers check (always applied)
    if parsed:
        parsed_path = parsed.path.lower()
        if re.search(r'/(en|es|fr|de|it|ja|zh|ko|ru|pt)/', parsed_path) or "lang=" in parsed.query.lower():
            score -= 5.0
            reasons.append("Language switcher penalty (-5)")

    # F. URL quality bonuses/penalties
    if len(url) < 60:
        score += 2.0
        reasons.append("Short URL bonus (+2)")
        
    if len(path_words) > 0:
        score += 2.0
        reasons.append("URL path has meaningful words (+2)")
        
    if len(query_params) > 2:
        score -= 2.0
        reasons.append("Too many query parameters (-2)")
        
    tracking_words = ["utm_", "ref=", "click", "source=", "medium="]
    if any(tw in url.lower() for tw in tracking_words):
        score -= 3.0
        reasons.append("Tracking URL penalty (-3)")
        
    if parsed:
        path_clean = parsed.path.strip("/")
        if path_clean and "/" not in path_clean:
            score += 1.0
            reasons.append("Homepage child depth (+1)")

    reason_str = "; ".join(reasons) if reasons else "Generic URL quality defaults."
    return {
        "score": score,
        "matched_terms": matched_terms,
        "reason": reason_str
    }
