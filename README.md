# Eco

[![CI](https://github.com/lizasodev/eco/actions/workflows/ci.yml/badge.svg)](https://github.com/lizasodev/eco/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Tu segundo cerebro local: pregúntale a tu yo del pasado.**

> *"¿Qué comando usé para arreglar el Bluetooth hace dos semanas?"* → `eco search bluetooth`

Eco registra de forma pasiva los comandos que ejecutas y las ventanas que usas, y te permite buscarlos después con contexto temporal. **Todo es local**: sin red, sin telemetría, sin dependencias. Ver [PRIVACY.md](PRIVACY.md) y [SECURITY.md](SECURITY.md).

## Instalación
Requiere Python ≥ 3.11 y Linux (el daemon de ventanas requiere Hyprland).

    git clone https://github.com/lizasodev/eco && cd eco
    python3 -m venv .venv && .venv/bin/pip install .
    ln -s "$PWD/.venv/bin/eco" ~/.local/bin/eco
    echo 'eval "$(eco hook bash)"' >> ~/.bashrc      # o: eco hook zsh >> ~/.zshrc

## Uso
    eco daemon                         # observa la ventana activa (déjalo en el autostart de Hyprland)
    eco search bluetooth               # búsqueda por palabras y prefijos
    eco search docker --kind cmd --since 7d
    eco around 42                      # qué pasaba 15 min antes/después del evento 42
    eco timeline --since 3h
    eco stats
    eco forget "mi-cliente"            # borra todo lo que coincida
    eco purge --older-than 90d

## Privacidad y seguridad en 30 segundos
- Datos en `~/.local/share/eco/eco.db`, permisos `0600`; carpeta `0700`.
- Los secretos (tokens, claves, `sudo`, gestores de contraseñas, ventanas de login/banco/incógnito) se descartan **antes** de escribir en disco.
- Cero dependencias en ejecución y cero conexiones de red.
- Detalle completo en [PRIVACY.md](PRIVACY.md) y [SECURITY.md](SECURITY.md).

## Hoja de ruta
- [x] Captura de comandos y ventanas + búsqueda de texto (v0.1)
- [ ] Búsqueda semántica con embeddings locales
- [ ] Capturas con OCR (opt-in) e interfaz con atajo global
- [ ] Línea de tiempo visual y respuestas con LLM local opcional

## Licencia
[MIT](LICENSE)
