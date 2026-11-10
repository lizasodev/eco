# Changelog

## 0.1.0 — 2026-11-10
Primera versión pública.
- Captura de comandos de terminal (hooks de bash y zsh) con carpeta y código de salida.
- Captura de la ventana activa en Hyprland (`eco daemon`).
- Búsqueda de texto completo con SQLite FTS5 (`eco search`), contexto temporal (`eco around`, `eco timeline`).
- Privacidad: filtros de secretos y ventanas sensibles antes de escribir en disco; `eco forget` y `eco purge`.
- Seguridad: base de datos con permisos `0600`, carpeta `0700`, `secure_delete`, sin dependencias externas ni red.
