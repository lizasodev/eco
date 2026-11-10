# Privacidad

Eco es **local-first**: todo se guarda en `~/.local/share/eco/eco.db` (o `$XDG_DATA_HOME/eco`) y **nunca sale de tu máquina**. No hay cuentas, servidores ni telemetría.

## Qué se guarda
| Tipo | Contenido |
|---|---|
| `cmd` | texto del comando, carpeta actual, código de salida, hora |
| `window` | título y aplicación de la ventana activa (Hyprland), hora |

No se guardan: la salida de los comandos, el contenido de las ventanas, pulsaciones de teclas ni capturas de pantalla (esto último llegará más adelante y será opcional).

## Qué NUNCA se guarda
Se descarta **antes de escribir en disco**:
- Comandos con contraseñas, tokens, claves de API (AWS, GitHub, OpenAI/Anthropic, Slack), JWT, claves privadas, URLs con `usuario:clave@`, autenticación básica, o que usen `sudo`, `pass`, `gpg`, `age`, `openssl`, `sops`, `bw`, `op`, `vault`, `ssh-add`.
- Ventanas de gestores de contraseñas (KeePassXC, Bitwarden, 1Password, Proton Pass…).
- Ventanas cuyo título indique login, banco, PayPal, navegación privada/incógnito, 2FA/OTP o frases semilla.
- Comandos de más de 2000 caracteres.

La lista completa está en [`src/eco/privacy.py`](src/eco/privacy.py). Son heurísticas: **revisa y amplía** esa lista según tu caso.

## Control total sobre tus datos
    eco stats                     # qué hay guardado
    eco forget "palabra"          # borra todo lo que coincida (con sobrescritura segura)
    eco purge --older-than 90d    # borra lo antiguo
    rm -r ~/.local/share/eco      # borra todo

Para dejar de registrar: quita la línea `eval "$(eco hook ...)"` de tu `.bashrc`/`.zshrc` y detén `eco daemon`.
