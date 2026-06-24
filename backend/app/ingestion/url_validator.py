import re
import socket
import ipaddress
from urllib.parse import urlparse

def normalize_url(url: str) -> str:
    """
    Normalizes a given URL string.
    - Strips leading and trailing spaces.
    - Prepend 'https://' if it does not start with http:// or https:// (and doesn't have another scheme).
    - Removes URL fragments (e.g. #section).
    """
    if not url:
        return ""
        
    url = url.strip()
    
    # Check if the URL already has a scheme prefix case-insensitively
    lower_url = url.lower()
    if not (lower_url.startswith("http://") or lower_url.startswith("https://")):
        # If it has another valid scheme structure (e.g. ftp://, file://), we leave it
        # as is so that the validator can catch and reject the unsupported scheme.
        if re.match(r'^[a-zA-Z][a-zA-Z0-9.+-]*://', url):
            pass
        else:
            url = "https://" + url

    # Remove URL fragment if present
    url = url.split("#")[0]
    return url

def validate_url(url: str) -> dict:
    """
    Validates a URL for safety against SSRF and malformed structures.
    Rejects:
    - Empty URLs
    - Protocols other than http and https (e.g., file://, ftp://)
    - Localhost, 127.0.0.1, 0.0.0.0
    - Private IP addresses (10.x.x.x, 172.16.x.x-172.31.x.x, 192.168.x.x)
    - Unresolved or syntactically invalid domains
    """
    if not url or url.strip() == "":
        return {
            "valid": False,
            "normalized_url": None,
            "message": "URL cannot be empty."
        }

    # Normalize the URL first
    normalized = normalize_url(url)

    try:
        parsed = urlparse(normalized)
    except Exception as e:
        return {
            "valid": False,
            "normalized_url": None,
            "message": f"Malformed URL format: {str(e)}"
        }

    # Validate Scheme
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        return {
            "valid": False,
            "normalized_url": None,
            "message": f"Unsupported scheme '{scheme}'. Only http and https are allowed."
        }

    # Extract hostname
    hostname = parsed.hostname
    if not hostname:
        return {
            "valid": False,
            "normalized_url": None,
            "message": "URL does not contain a valid hostname."
        }

    hostname = hostname.lower()

    # Reject localhost by name
    if hostname == "localhost":
        return {
            "valid": False,
            "normalized_url": None,
            "message": "Localhost access is restricted."
        }

    # Evaluate hostname to prevent SSRF (Local/Private IP ranges)
    try:
        # Check if the hostname is a direct IP address
        ip_obj = ipaddress.ip_address(hostname)
        is_direct_ip = True
    except ValueError:
        is_direct_ip = False

    resolved_ip = None
    if is_direct_ip:
        resolved_ip = ip_obj
    else:
        # Resolve the domain to an IP address (safely catches invalid domains)
        try:
            ip_str = socket.gethostbyname(hostname)
            resolved_ip = ipaddress.ip_address(ip_str)
        except socket.gaierror:
            return {
                "valid": False,
                "normalized_url": None,
                "message": f"Invalid domain: Hostname '{hostname}' could not be resolved."
            }
        except Exception as e:
            return {
                "valid": False,
                "normalized_url": None,
                "message": f"Failed to resolve domain: {str(e)}"
            }

    # Verify IP address safety
    if resolved_ip:
        if resolved_ip.is_loopback:
            return {
                "valid": False,
                "normalized_url": None,
                "message": f"Access to loopback IP address '{resolved_ip}' is restricted."
            }
        if resolved_ip.is_private:
            return {
                "valid": False,
                "normalized_url": None,
                "message": f"Access to private IP address range '{resolved_ip}' is restricted."
            }
        if resolved_ip.is_unspecified:
            return {
                "valid": False,
                "normalized_url": None,
                "message": f"Access to unspecified IP address '{resolved_ip}' is restricted."
            }

    return {
        "valid": True,
        "normalized_url": normalized,
        "message": "URL is valid"
    }

if __name__ == "__main__":
    test_urls = [
        "python.org",
        "https://www.python.org/downloads/#windows",
        "localhost:8000",
        "http://127.0.0.1:8000",
        "ftp://example.com",
        "file:///C:/test.txt",
        "192.168.1.1",
        "invalid url"
    ]

    print("=" * 60)
    print("Running URL Validator self-tests...")
    print("=" * 60)

    for test_url in test_urls:
        print(f"\nTesting Input: {test_url}")
        result = validate_url(test_url)
        if result["valid"]:
            print(f"  SUCCESS: Valid URL!")
            print(f"  Normalized URL: {result['normalized_url']}")
            print(f"  Message:        {result['message']}")
        else:
            print(f"  REJECTED: Invalid URL!")
            print(f"  Message:        {result['message']}")

    print("\n" + "=" * 60)
    print("Self-tests completed!")
    print("=" * 60)
