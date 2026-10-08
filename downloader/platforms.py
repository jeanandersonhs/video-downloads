from urllib.parse import urlparse

PLATFORMS = {
    "tiktok": ("tiktok.com",),
    "instagram": ("instagram.com",),
    "twitter": ("twitter.com", "x.com"),
}


def normalize(url: str) -> str:
    url = url.strip()
    if url and "://" not in url:
        url = "https://" + url
    return url


def detect(url: str) -> str | None:
    """Retorna 'tiktok', 'instagram' ou 'twitter' (ou None se não suportado)."""
    host = (urlparse(normalize(url)).hostname or "").lower()
    for name, domains in PLATFORMS.items():
        if any(host == d or host.endswith("." + d) for d in domains):
            return name
    return None
