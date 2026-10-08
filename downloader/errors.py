LOGIN_HINTS = (
    "login", "log in", "sign in", "cookies", "authentication",
    "rate-limit", "rate limit", "requested content is not available",
    "restricted video", "age-restricted", "empty media response",
)


def _message(exc: BaseException) -> str:
    return str(exc).replace("ERROR: ", "").strip()


def needs_login(exc: BaseException) -> bool:
    msg = _message(exc).lower()
    return any(hint in msg for hint in LOGIN_HINTS)


def classify(exc: BaseException) -> tuple[str, int]:
    """Retorna (código, status HTTP) para um erro do yt-dlp/rede."""
    low = _message(exc).lower()
    if needs_login(exc):
        return "login_required", 422
    if "private" in low:
        return "private", 404
    if "unsupported url" in low:
        return "unsupported", 400
    if any(w in low for w in ("unavailable", "not exist", "removed", "404", "no video")):
        return "unavailable", 404
    if any(w in low for w in ("urlopen", "network", "timed out", "name resolution", "connection")):
        return "network", 502
    return "unknown", 502


def friendly(exc: BaseException) -> str:
    """Traduz erros comuns do yt-dlp/rede para mensagens curtas."""
    code = classify(exc)[0]
    messages = {
        "login_required": "Este conteúdo exige login ou o acesso foi bloqueado pela plataforma. "
                          "Tente novamente mais tarde ou use outro link.",
        "private": "O vídeo é privado.",
        "unsupported": "Link não suportado ou sem vídeo.",
        "unavailable": "O vídeo não está disponível (removido ou link incorreto).",
        "network": "Falha de rede ao acessar a plataforma. Tente novamente.",
    }
    if code in messages:
        return messages[code]
    msg = _message(exc)
    return msg.splitlines()[0] if msg else "Erro desconhecido."
