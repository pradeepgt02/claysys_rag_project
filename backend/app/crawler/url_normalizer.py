from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

def normalize_crawl_url(url: str) -> str:
    """
    Cleans and standardizes crawl URLs:
    - Removes URL fragments (e.g. #section).
    - Removes common tracking query parameters (utm_*, gclid, fbclid).
    - Retains other useful query parameters.
    - Lowercases scheme and netloc.
    - Appends trailing slashes to homepages and directory-like paths consistently.
    """
    url = url.strip()
    if not url:
        return ""

    # Remove URL fragments
    url = url.split('#')[0]

    try:
        parsed = urlparse(url)
    except Exception:
        return url

    # Clean tracking query parameters
    tracking_params = {
        'utm_source', 'utm_medium', 'utm_campaign', 
        'utm_term', 'utm_content', 'gclid', 'fbclid'
    }

    new_query = ""
    if parsed.query:
        query_params = parse_qsl(parsed.query, keep_blank_values=True)
        filtered_params = [(k, v) for k, v in query_params if k.lower() not in tracking_params]
        if filtered_params:
            new_query = urlencode(filtered_params)

    # Normalize path: homepage or directory trailing slash rules
    path = parsed.path
    if not path or path == "":
        path = "/"
    elif path == "/":
        path = "/"
    else:
        # Check if the path is directory-like (e.g. doesn't have a file extension like .html)
        last_segment = path.split('/')[-1]
        if '.' not in last_segment:
            if not path.endswith('/'):
                path = path + '/'

    # Reassemble URL
    normalized = urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        path,
        parsed.params,
        new_query,
        ""  # fragment is stripped
    ))

    return normalized


def is_same_domain(url: str, base_domain: str) -> bool:
    """
    Checks if a URL belongs to the same domain or a subdomain of the base domain.
    """
    if not url or not base_domain:
        return False

    try:
        parsed_url = urlparse(url)
        url_host = parsed_url.hostname
        if not url_host:
            return False
        url_host = url_host.lower()

        base_host = base_domain.lower()
        # Parse base domain in case a full URL is passed as the base_domain
        if "://" in base_host:
            base_parsed = urlparse(base_host)
            base_host = base_parsed.hostname or base_host

        # Match exact hostname or a subdomain extension
        if url_host == base_host:
            return True
        if url_host.endswith("." + base_host):
            return True

        return False
    except Exception:
        return False

def is_crawlable_url(url: str) -> bool:
    """
    Filters URLs to ensure they use standard HTTP/HTTPS and do not point to
    static media files, documents, binaries, scripts, or non-web schemas.
    """
    if not url:
        return False

    try:
        parsed = urlparse(url)
    except Exception:
        return False

    # Restrict scheme
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        return False

    path = parsed.path.lower()

    # Define disallowed extensions
    excluded_extensions = {
        # Images
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".bmp", ".tiff",
        # Code assets
        ".css", ".js",
        # Fonts
        ".woff", ".woff2", ".ttf", ".otf", ".eot",
        # Media files
        ".mp4", ".mkv", ".webm", ".avi", ".mov", ".flv", ".wmv",
        ".mp3", ".wav", ".aac", ".ogg", ".flac", ".m4a",
        # Archive formats
        ".zip", ".rar", ".7z", ".tar", ".gz", ".tar.gz",
        # Binaries
        ".exe", ".apk", ".dmg", ".msi", ".bin",
        # Document downloads
        ".docx", ".xlsx", ".pptx", ".doc", ".xls", ".ppt", ".pdf"
    }

    # Reject if path ends with any excluded extensions
    for ext in excluded_extensions:
        if path.endswith(ext):
            return False

    # Reject if missing hostname
    if not parsed.hostname:
        return False

    return True
