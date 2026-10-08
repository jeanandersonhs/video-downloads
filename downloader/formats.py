import os
from dataclasses import asdict, dataclass

from . import tiktok

COOKIES_PATH = "/tmp/cookies.txt"
PROGRESSIVE_PROTOCOLS = (None, "http", "https")


@dataclass
class Quality:
    id: str
    label: str
    height: int | None = None
    ext: str | None = None
    size: int | None = None  # bytes, quando conhecido

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_info(url: str) -> dict:
    import yt_dlp

    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "cachedir": False,  # filesystem da Vercel é somente leitura
    }
    if proxy := os.environ.get("PROXY_URL"):
        opts["proxy"] = proxy
    if cookies := os.environ.get("COOKIES_TXT"):
        with open(COOKIES_PATH, "w") as f:
            f.write(cookies)
        opts["cookiefile"] = COOKIES_PATH
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        _attach_cookies(info, ydl.cookiejar)
        return info


def _attach_cookies(info: dict, cookiejar) -> None:
    """Os CDNs (ex.: TikTok) respondem 403 sem os cookies da sessão de extração."""
    for fmt in info.get("formats") or []:
        header = cookiejar.get_cookie_header(fmt["url"]) if fmt.get("url") else None
        if header:
            fmt["http_headers"] = {**(fmt.get("http_headers") or {}), "Cookie": header}


def _size(fmt: dict) -> int | None:
    return fmt.get("filesize") or fmt.get("filesize_approx")


def _score(fmt: dict) -> float:
    return fmt.get("tbr") or fmt.get("vbr") or 0


def _resolution(fmt: dict, height: int) -> int:
    """Vídeos verticais (TikTok 720x1280) são conhecidos como 720p, não 1280p."""
    width = fmt.get("width")
    return min(width, height) if width else height


def progressive_formats(info: dict, platform: str) -> list[dict]:
    """Formatos de arquivo único (vídeo+áudio) servidos por HTTP: baixáveis sem ffmpeg."""
    result = []
    for fmt in info.get("formats") or []:
        if not fmt.get("url") or not fmt.get("format_id"):
            continue
        if fmt.get("vcodec") == "none" or fmt.get("acodec") == "none":
            continue
        if fmt.get("protocol") not in PROGRESSIVE_PROTOCOLS:
            continue
        result.append(fmt)
    if platform == "tiktok":
        result = tiktok.without_watermark(result)
    return result


def build_qualities(info: dict, platform: str) -> list[Quality]:
    """Uma opção por resolução (a de maior bitrate)."""
    formats = progressive_formats(info, platform)

    best_by_height: dict[int, dict] = {}
    for fmt in formats:
        height = fmt.get("height")
        if not height:
            continue
        if height not in best_by_height or _score(fmt) > _score(best_by_height[height]):
            best_by_height[height] = fmt

    qualities = [
        Quality(id=fmt["format_id"], label=f"{_resolution(fmt, height)}p", height=height,
                ext=fmt.get("ext"), size=_size(fmt))
        for height, fmt in sorted(best_by_height.items(), reverse=True)
    ]
    if not qualities and formats:
        best = max(formats, key=_score)
        qualities.append(Quality(id=best["format_id"], label="Melhor disponível",
                                 ext=best.get("ext"), size=_size(best)))
    return qualities


def find_format(info: dict, platform: str, format_id: str) -> dict | None:
    """Só aceita ids que o servidor ofereceria (progressivos, sem marca d'água)."""
    return next((f for f in progressive_formats(info, platform) if f["format_id"] == format_id), None)
