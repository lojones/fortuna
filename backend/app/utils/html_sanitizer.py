import logging
import re
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Allowlisted CDN domains for external scripts
ALLOWED_CDN_DOMAINS = [
    "cdn.jsdelivr.net",
    "cdnjs.cloudflare.com",
    "unpkg.com",
    "d3js.org",
    "cdn.plot.ly",
]

# Suspicious patterns to flag
SUSPICIOUS_PATTERNS = [
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=\s*[\"'].*fetch\s*\(", re.IGNORECASE),
    re.compile(r"document\.cookie", re.IGNORECASE),
    re.compile(r"window\.location\s*=", re.IGNORECASE),
]


def check_html_safety(html_content: str) -> Tuple[bool, List[str]]:
    """
    Perform basic safety checks on LLM-generated HTML.
    Returns (is_safe, list_of_warnings).
    """
    warnings = []

    # Check for suspicious patterns
    for pattern in SUSPICIOUS_PATTERNS:
        matches = pattern.findall(html_content)
        if matches:
            warnings.append(f"Suspicious pattern detected: {pattern.pattern}")

    # Check for external script sources not in allowlist
    script_src_pattern = re.compile(
        r'<script[^>]+src\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE
    )
    for match in script_src_pattern.finditer(html_content):
        src = match.group(1)
        if src.startswith("http://") or src.startswith("https://"):
            domain = src.split("/")[2] if len(src.split("/")) > 2 else ""
            if domain and not any(
                domain.endswith(allowed) for allowed in ALLOWED_CDN_DOMAINS
            ):
                warnings.append(f"External script from non-allowlisted domain: {domain}")

    if warnings:
        for w in warnings:
            logger.warning(f"HTML safety check: {w}")

    # For now, we log warnings but don't reject — this could be made strict
    return (len(warnings) == 0, warnings)
