"""Input validation helpers."""
import re
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs


YOUTUBE_PATTERNS = [
    r"(?:youtube(?:-nocookie)?\.com/(?:watch\?v=|embed/|shorts/)|youtu\.be/)([a-zA-Z0-9_-]{11})",
    r"youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
    r"youtube\.com/live/([a-zA-Z0-9_-]{11})",
    r"music\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
]


def extract_youtube_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from URL."""
    if not url:
        return None
    url = url.strip()
    # Direct 11-char ID
    if re.match(r"^[a-zA-Z0-9_-]{11}$", url):
        return url

    # Try quick regex patterns first
    for pattern in YOUTUBE_PATTERNS:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    # Fallback to URL parsing for more exotic forms (youtu.be with params, studio links, etc.)
    try:
        parsed = urlparse(url)
    except Exception:
        return None

    netloc = (parsed.netloc or "").lower()
    path = (parsed.path or "").lstrip("/")

    # Short youtu.be links: path starts with the ID
    if "youtu.be" in netloc and path:
        candidate = path.split("/")[0]
        if re.match(r"^[a-zA-Z0-9_-]{11}$", candidate):
            return candidate
        if len(candidate) >= 11:
            return candidate[:11]

    # Standard youtube.com links
    if "youtube" in netloc or "youtube-nocookie" in netloc:
        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            return qs["v"][0][:11]

        # Paths like /embed/ID or /shorts/ID or /watch/ID
        parts = path.split("/")
        for key in ("embed", "shorts", "watch", "live"):
            if key in parts:
                idx = parts.index(key)
                if idx + 1 < len(parts):
                    cand = parts[idx + 1]
                    if re.match(r"^[a-zA-Z0-9_-]{11}$", cand):
                        return cand
                    if len(cand) >= 11:
                        return cand[:11]

    return None


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email or ""))


def validate_password(password: str) -> Tuple[bool, str]:
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain an uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain a lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain a digit"
    return True, ""


def validate_language(lang: str) -> bool:
    return lang in ("en", "hi", "pa", "bho")
