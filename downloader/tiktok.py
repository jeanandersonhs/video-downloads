"""TikTok sem marca d'água.

Primário: yt-dlp expõe o formato "download" (com logo no final) e os formatos de
reprodução (sem logo). Ficamos só com os sem logo.
Fallback: API pública de terceiros (tikwm) que devolve a URL do vídeo sem logo.
"""
import json
import urllib.parse
import urllib.request

TIKWM_API = "https://www.tikwm.com/api/?hd=1&url="
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
FALLBACK_PREFIX = "tikwm:"


def is_watermarked(fmt: dict) -> bool:
    # yt-dlp: o extractor web usa format_id "download" (note "watermarked"); o da API mobile
    # marca "Download video, watermarked" em `download_addr` só quando has_watermark é verdadeiro.
    return fmt.get("format_id") == "download" or "watermark" in (fmt.get("format_note") or "").lower()


def without_watermark(formats: list[dict]) -> list[dict]:
    return [f for f in formats if not is_watermarked(f)]


def fetch_fallback(url: str) -> dict:
    """Consulta o serviço externo.

    Retorna {'id', 'title', 'thumbnail', 'options': [{'id', 'label', 'url'}]}.
    """
    req = urllib.request.Request(TIKWM_API + urllib.parse.quote(url, safe=""),
                                 headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.load(resp)
    data = payload.get("data")
    if payload.get("code") != 0 or not data:
        raise RuntimeError(payload.get("msg") or "serviço alternativo não retornou o vídeo")

    options = []
    if data.get("hdplay"):
        options.append({"id": FALLBACK_PREFIX + "hd", "label": "HD", "url": data["hdplay"]})
    if data.get("play"):
        options.append({"id": FALLBACK_PREFIX + "play", "label": "Padrão", "url": data["play"]})
    if not options:
        raise RuntimeError("serviço alternativo não retornou URL de vídeo")
    return {
        "id": str(data.get("id") or "tiktok"),
        "title": data.get("title") or "",
        "thumbnail": data.get("cover"),
        "options": options,
    }
