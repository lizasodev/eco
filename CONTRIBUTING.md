# Contribuir

1. Haz fork y crea una rama.
2. `python -m venv .venv && .venv/bin/pip install -e . pytest && .venv/bin/pytest`
3. Mantén la regla de oro: **sin dependencias en ejecución y sin red**. Cualquier cambio que toque privacidad (`privacy.py`) debe llevar tests.
4. Abre un pull request. Las vulnerabilidades se reportan en privado: ver [SECURITY.md](SECURITY.md).
