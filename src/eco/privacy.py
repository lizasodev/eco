"""Filtros de privacidad: lo que NUNCA se guarda.

Filosofía: ante la duda, descartar. Es preferible perder un comando inocuo
que guardar un secreto. Todo el filtrado ocurre ANTES de escribir en disco.

Puedes añadir tus propias reglas (una expresión regular por línea) en
``~/.config/eco/privacy.txt``. Líneas vacías y las que empiezan por ``#`` se ignoran.
Prefijos opcionales: ``cmd:`` (solo comandos) o ``window:`` (solo títulos de ventana).
"""
import os
import re
from functools import lru_cache
from pathlib import Path

# Clases de ventana (app_id) ignoradas por completo.
IGNORED_CLASSES = {
    "keepassxc", "org.keepassxc.keepassxc", "bitwarden", "1password",
    "org.gnome.seahorse.application", "proton-pass", "enpass", "keepass2",
    "org.gnome.seahorse", "gnome-keyring", "lockscreen", "hyprlock", "swaylock",
}

# Si el título de la ventana contiene alguno de estos, se ignora.
IGNORED_TITLE = re.compile(
    r"(password|contrase[ñn]a|clave de acceso|banco|bank|banca|paypal|bizum|revolut|wise\b"
    r"|login|log in|sign in|sign up|iniciar sesi[oó]n|identificaci[oó]n"
    r"|incognito|inc[oó]gnito|privad[ao]|private browsing|2fa|otp|authenticator"
    r"|verification code|c[oó]digo de verificaci[oó]n|recovery code|c[oó]digo de recuperaci[oó]n"
    r"|seed phrase|frase semilla|wallet|cartera|tarjeta|card number|cvv|iban"
    r"|api key|access token|secret|credential|\.env\b|id_rsa|id_ed25519|\.pem\b|\.kdbx\b)",
    re.IGNORECASE,
)

# Comandos que probablemente contienen secretos: se descartan enteros.
SECRET_CMD = re.compile(
    r"("
    r"password|passwd|passphrase|secret|token|api[_-]?key|credential|private[_-]?key|auth"
    r"|authorization:|bearer\s|x-api-key|set-cookie|cookie:"
    r"|\b(curl|http|wget)\b.*\s(-u|--user)\b"                      # basic auth
    r"|\b(mysql|mariadb|psql|mongosh|redis-cli)\b.*\s(-p\S|-W\b|--password)"
    r"|\b(docker|podman|npm|pnpm|yarn|pip|twine|cargo|gh|glab|aws|gcloud|az|kubectl|helm|terraform|nmcli|iwctl|wpa_cli)\b"
    r".*\b(login|auth|adduser|credentials|configure|set-credentials|psk|wifi|connect)\b"
    r"|\b(pass|gpg|age|openssl|sops|bw|op|vault|ssh-add|ssh-keygen|sudo|doas|su|keyctl|secret-tool)\b"
    r"|\.(env|pem|key|kdbx|p12|pfx|gpg|asc)\b|id_(rsa|ed25519|ecdsa|dsa)\b"
    r"|\b(export|set|declare|env)\b\s+\w*(key|secret|pass|pwd|token)\w*="
    r")",
    re.IGNORECASE,
)

# Valores sensibles que pueden aparecer en CUALQUIER texto (comandos y títulos).
SENSITIVE_VALUE = re.compile(
    r"("
    r"AKIA[0-9A-Z]{12,}|ASIA[0-9A-Z]{12,}"                         # AWS
    r"|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"    # GitHub
    r"|glpat-[A-Za-z0-9_-]{15,}|npm_[A-Za-z0-9]{30,}"              # GitLab, npm
    r"|sk-[A-Za-z0-9_-]{20,}|[sr]k_(live|test)_[A-Za-z0-9]{10,}"   # OpenAI/Anthropic, Stripe
    r"|AIza[0-9A-Za-z_-]{30,}"                                     # Google
    r"|xox[baprs]-[A-Za-z0-9-]{10,}|hooks\.slack\.com/services/\S+"  # Slack
    r"|discord(app)?\.com/api/webhooks/\S+"
    r"|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}"  # JWT
    r"|-----BEGIN [A-Z ]*PRIVATE KEY"
    r"|://[^/\s:@]+:[^/\s@]+@"                                     # user:pass@host
    r"|\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){3,7}(?:[ ]?[A-Z0-9]{1,4})?\b"  # IBAN
    r"|\b\d{8}[A-HJ-NP-TV-Z]\b|\b[XYZ]\d{7}[A-HJ-NP-TV-Z]\b"       # DNI / NIE
    r")"
)
_CARD = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_LONG_TOKEN = re.compile(r"(?<![\w/.-])[A-Za-z0-9_+=-]{32,}(?![\w/.-])")
_HEX = re.compile(r"^[0-9a-fA-F]+$")

MAX_COMMAND_LEN = 2000


def _luhn(digits: str) -> bool:
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d = d * 2 - 9 if d * 2 > 9 else d * 2
        total += d
        alt = not alt
    return total % 10 == 0


def _has_card(text: str) -> bool:
    return any(13 <= len(d) <= 19 and _luhn(d)
               for m in _CARD.finditer(text) for d in ["".join(c for c in m.group() if c.isdigit())])


def _has_opaque_token(text: str) -> bool:
    """Cadenas largas tipo clave (mezcla de letras y números). Los hashes hex puros (git) se permiten."""
    for m in _LONG_TOKEN.finditer(text):
        t = m.group()
        if not _HEX.match(t) and any(c.isdigit() for c in t) and any(c.isalpha() for c in t):
            return True
    return False


def sensitive_value(text: str) -> bool:
    return bool(SENSITIVE_VALUE.search(text)) or _has_card(text) or _has_opaque_token(text)


@lru_cache(maxsize=1)
def _custom_rules():
    """Reglas del usuario. Una regex inválida se ignora (nunca rompe el registro)."""
    path = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "eco" / "privacy.txt"
    rules = {"cmd": [], "window": []}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return rules
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        scope = "both"
        for prefix in ("cmd:", "window:"):
            if line.startswith(prefix):
                scope, line = prefix[:-1], line[len(prefix):]
        try:
            rx = re.compile(line, re.IGNORECASE)
        except re.error:
            continue
        for k in ("cmd", "window"):
            if scope in ("both", k):
                rules[k].append(rx)
    return rules


def window_allowed(cls: str, title: str) -> bool:
    title = title or ""
    return (cls.lower() not in IGNORED_CLASSES
            and not IGNORED_TITLE.search(title)
            and not sensitive_value(title)
            and not any(rx.search(title) or rx.search(cls) for rx in _custom_rules()["window"]))


def command_allowed(cmd: str) -> bool:
    return (len(cmd) <= MAX_COMMAND_LEN
            and not SECRET_CMD.search(cmd)
            and not sensitive_value(cmd)
            and not any(rx.search(cmd) for rx in _custom_rules()["cmd"]))
