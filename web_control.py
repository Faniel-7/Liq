import re
import webbrowser
from urllib.parse import quote_plus

SITE_DATA = {
    "google": {
        "label": "Google",
        "open": "https://www.google.com",
        "search": "https://www.google.com/search?q={query}",
    },
    "youtube": {
        "label": "YouTube",
        "open": "https://www.youtube.com",
        "search": "https://www.youtube.com/results?search_query={query}",
    },
    "github": {
        "label": "GitHub",
        "open": "https://github.com",
        "search": "https://github.com/search?q={query}",
    },
    "stack overflow": {
        "label": "Stack Overflow",
        "open": "https://stackoverflow.com",
        "search": "https://stackoverflow.com/search?q={query}",
    },
    "reddit": {
        "label": "Reddit",
        "open": "https://www.reddit.com",
        "search": "https://www.reddit.com/search/?q={query}",
    },
    "google maps": {
        "label": "Google Maps",
        "open": "https://www.google.com/maps",
        "search": "https://www.google.com/maps/search/{query}",
    },
    "gmail": {
        "label": "Gmail",
        "open": "https://mail.google.com",
        "search": None,
    },
    "chatgpt": {
        "label": "ChatGPT",
        "open": "https://chatgpt.com",
        "search": None,
    },
    "openai": {
        "label": "OpenAI",
        "open": "https://openai.com",
        "search": None,
    },
    "facebook": {
        "label": "Facebook",
        "open": "https://www.facebook.com",
        "search": None,
    },
    "instagram": {
        "label": "Instagram",
        "open": "https://www.instagram.com",
        "search": None,
    },
    "linkedin": {
        "label": "LinkedIn",
        "open": "https://www.linkedin.com",
        "search": None,
    },
    "netflix": {
        "label": "Netflix",
        "open": "https://www.netflix.com",
        "search": None,
    },
    "spotify": {
        "label": "Spotify",
        "open": "https://open.spotify.com",
        "search": None,
    },
    "whatsapp": {
        "label": "WhatsApp",
        "open": "https://web.whatsapp.com",
        "search": None,
    },
    "wikipedia": {
        "label": "Wikipedia",
        "open": "https://www.wikipedia.org",
        "search": "https://en.wikipedia.org/w/index.php?search={query}",
    },
    "drive": {
        "label": "Google Drive",
        "open": "https://drive.google.com",
        "search": None,
    },
    "docs": {
        "label": "Google Docs",
        "open": "https://docs.google.com",
        "search": None,
    },
}

SITE_ALIASES = [
    ("google maps", ["google maps", "maps"]),
    ("stack overflow", ["stack overflow", "stackoverflow"]),
    ("google", ["google"]),
    ("youtube", ["youtube", "yt"]),
    ("github", ["github"]),
    ("reddit", ["reddit"]),
    ("gmail", ["gmail"]),
    ("chatgpt", ["chatgpt"]),
    ("openai", ["openai"]),
    ("facebook", ["facebook"]),
    ("instagram", ["instagram"]),
    ("linkedin", ["linkedin"]),
    ("netflix", ["netflix"]),
    ("spotify", ["spotify"]),
    ("whatsapp", ["whatsapp", "whatsapp web"]),
    ("wikipedia", ["wikipedia"]),
    ("drive", ["drive"]),
    ("docs", ["docs"]),
]

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())

def _match_site(text: str):
    normalized = _normalize(text)

    for canonical, aliases in SITE_ALIASES:
        for alias in aliases:
            pattern = rf"\b{re.escape(alias)}\b"
            if re.search(pattern, normalized):
                return canonical

    return None

def _open_url(url: str):
    try:
        webbrowser.open(url, new=2)
        return True, "Opened successfully."
    except Exception as e:
        return False, f"I couldn't open it: {e}"

def _open_site(site_key: str):
    site = SITE_DATA.get(site_key)
    if site is None:
        return False, "I don't know that website yet."

    return _open_url(site["open"])

def _search_site(site_key: str, query: str):
    site = SITE_DATA.get(site_key)
    if site is None:
        return False, "I don't know that website yet."

    template = site.get("search")
    if not template:
        return False, f"{site['label']} does not support search in Liq yet."

    url = template.format(query=quote_plus(query))
    success, _ = _open_url(url)
    if success:
        return True, f"Searching {site['label']} for {query}."
    return False, f"I couldn't search {site['label']}."

def parse_web_command(user_input: str):
    text = _normalize(user_input)

    m = re.match(r"^(?:search|find)\s+(.+?)\s+for\s+(.+)$", text)
    if m:
        site_phrase = m.group(1).strip()
        query = m.group(2).strip()
        site = _match_site(site_phrase)
        if site:
            return {"action": "search", "site": site, "query": query}

    m = re.match(r"^(?:search|find|open)\s+(.+?)\s+(?:on|in)\s+(.+)$", text)
    if m:
        query = m.group(1).strip()
        site_phrase = m.group(2).strip()
        site = _match_site(site_phrase)
        if site:
            return {"action": "search", "site": site, "query": query}

    m = re.match(r"^(?:open|visit|go to|launch)\s+(.+)$", text)
    if m:
        target = m.group(1).strip()
        site = _match_site(target)
        if site:
            return {"action": "open", "site": site}

    m = re.match(r"^(?:search|find)\s+(.+)$", text)
    if m:
        query = m.group(1).strip()
        return {"action": "search", "site": "google", "query": query}

    return None

def handle_web_command(user_input: str):
    parsed = parse_web_command(user_input)

    if parsed is None:
        return None

    action = parsed["action"]
    site = parsed["site"]

    if action == "open":
        return _open_site(site)

    if action == "search":
        return _search_site(site, parsed["query"])

    return None