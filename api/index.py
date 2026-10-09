from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse

from downloader import formats, platforms, stream, tiktok
from downloader.errors import classify, friendly

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

MAX_URL_LENGTH = 2048


class ApiError(Exception):
    def __init__(self, message: str, code: str, status: int):
        self.message, self.code, self.status = message, code, status


@app.exception_handler(ApiError)
def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse({"error": exc.message, "code": exc.code}, status_code=exc.status)


def _validate(url: str) -> tuple[str, str]:
    platform = platforms.detect(url)
    if not platform:
        raise ApiError("Link não suportado. Use links de TikTok, Instagram ou Twitter/X.", "unsupported", 400)
    return platform, platforms.normalize(url)


def _from_exception(exc: Exception) -> ApiError:
    code, status = classify(exc)
    return ApiError(friendly(exc), code, status)


def _tiktok_fallback(url: str) -> dict | None:
    try:
        return tiktok.fetch_fallback(url)
    except Exception:  # noqa: BLE001 - serviço de terceiros, qualquer falha vira "sem fallback"
        return None


@app.get("/api/info")
def info(url: str = Query(..., max_length=MAX_URL_LENGTH)):
    platform, url = _validate(url)

    meta: dict = {}
    qualities: list[formats.Quality] = []
    error: Exception | None = None
    try:
        data = formats.fetch_info(url)
        qualities = formats.build_qualities(data, platform)
        meta = {"title": data.get("title"), "thumbnail": data.get("thumbnail"), "duration": data.get("duration")}
    except Exception as exc:  # noqa: BLE001
        error = exc

    if platform == "tiktok" and not qualities:
        fallback = _tiktok_fallback(url)
        if fallback:
            qualities = [formats.Quality(id=o["id"], label=o["label"], ext="mp4") for o in fallback["options"]]
            meta = {"title": fallback["title"], "thumbnail": fallback["thumbnail"], "duration": None}

    if not qualities:
        if error:
            raise _from_exception(error)
        raise ApiError("Nenhuma qualidade baixável encontrada para este vídeo.", "no_formats", 422)

    return {"platform": platform, **meta, "qualities": [q.to_dict() for q in qualities]}


@app.get("/api/download")
def download(url: str = Query(..., max_length=MAX_URL_LENGTH), format: str = Query(..., max_length=128)):
    platform, url = _validate(url)

    if format.startswith(tiktok.FALLBACK_PREFIX):
        if platform != "tiktok":
            raise ApiError("Formato inválido.", "invalid_format", 400)
        data = _tiktok_fallback(url)
        option = next((o for o in (data or {}).get("options", []) if o["id"] == format), None)
        if not option:
            raise ApiError("Formato indisponível. Verifique o link novamente.", "invalid_format", 404)
        source_url, headers = option["url"], {"User-Agent": tiktok.USER_AGENT}
        filename = stream.safe_filename(data["title"], data["id"], "mp4")
    else:
        try:
            data = formats.fetch_info(url)
        except Exception as exc:  # noqa: BLE001
            raise _from_exception(exc) from exc
        fmt = formats.find_format(data, platform, format)
        if not fmt:
            raise ApiError("Formato indisponível. Verifique o link novamente.", "invalid_format", 404)
        source_url, headers = fmt["url"], fmt.get("http_headers") or {}
        filename = stream.safe_filename(data.get("title"), data.get("id"), fmt.get("ext"))

    try:
        client, resp = stream.open_stream(source_url, headers)
    except stream.BlockedURL as exc:
        raise ApiError("Origem do vídeo não permitida.", "blocked", 400) from exc
    except Exception as exc:  # noqa: BLE001
        raise ApiError(f"Não foi possível baixar o vídeo ({exc}).", "upstream", 502) from exc

    response_headers = {"Content-Disposition": stream.content_disposition(filename), "Cache-Control": "no-store"}
    if length := resp.headers.get("content-length"):
        response_headers["Content-Length"] = length
    media_type = stream.media_type(filename, resp.headers.get("content-type"))
    return StreamingResponse(stream.iterate(client, resp), media_type=media_type, headers=response_headers)
