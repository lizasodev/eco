"""Filtros de privacidad: lo que NUNCA se guarda.

Filosofía: ante la duda, descartar. Es preferible perder un comando inocuo
que guardar un secreto. Todo el filtrado ocurre ANTES de escribir en disco.
"""
import re

# Clases de ventana (app_id) ignoradas por completo.
IGNORED_CLASSES = {
    "keepassxc", "org.keepassxc.keepassxc", "bitwarden", "1password",
    "org.gnome.seahorse.application", "proton-pass", "enpass", "keepass2",
}

# Si el título de la ventana contiene alguno de estos, se ignora.
IGNORED_TITLE = re.compile(
    r"(password|contrase[ñn]a|banco|bank|paypal|login|log in|sign in|iniciar sesi[oó]n"
    r"|incognito|inc[oó]gnito|privad[ao]|private browsing|2fa|otp|verification code|seed phrase)",
    re.IGNORECASE,
)

# Comandos que probablemente contienen secretos: se descartan enteros.
SECRET_CMD = re.compile(
    r"("
    r"password|passwd|passphrase|secret|token|api[_-]?key|credential|private[_-]?key"
    r"|authorization:|bearer\s|x-api-key|set-cookie|cookie:"
    r"|AKIA[0-9A-Z]{12,}|ASIA[0-9A-Z]{12,}"                        # AWS
    r"|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"    # GitHub
    r"|sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,}"         # OpenAI/Anthropic, Slack
    r"|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}"  # JWT
    r"|-----BEGIN [A-Z ]*PRIVATE KEY"
    r"|://[^/\s:@]+:[^/\s@]+@"                                     # user:pass@host
    r"|\b(curl|http|wget)\b.*\s(-u|--user)\b"                      # basic auth
    r"|\b(pass|gpg|age|openssl|sops|bw|op|vault|ssh-add|sudo)\b"   # gestores / cifrado / sudo
    r")",
    re.IGNORECASE,
)

MAX_COMMAND_LEN = 2000


def window_allowed(cls: str, title: str) -> bool:
    return cls.lower() not in IGNORED_CLASSES and not IGNORED_TITLE.search(title or "")


def command_allowed(cmd: str) -> bool:
    return len(cmd) <= MAX_COMMAND_LEN and not SECRET_CMD.search(cmd)
