"""Observa la ventana activa de Hyprland y registra los cambios."""
import json
import subprocess
import time

from . import db, privacy


def active_window():
    try:
        out = subprocess.run(["hyprctl", "activewindow", "-j"], capture_output=True,
                             text=True, timeout=2).stdout
        w = json.loads(out) if out.strip() else {}
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None
    if not w or not w.get("class"):
        return None
    return w.get("class", ""), w.get("title", "")


def run(interval=2.0, min_seconds=3.0):
    con = db.connect()
    last, since = None, 0.0
    print(f"eco daemon: observando ventanas cada {interval}s (Ctrl+C para salir)")
    try:
        while True:
            cur = active_window()
            now = time.time()
            if cur != last:
                last, since = cur, now
            elif cur and since and now - since >= min_seconds:
                # Se registra una sola vez, cuando la ventana lleva estable min_seconds.
                cls, title = cur
                if privacy.window_allowed(cls, title):
                    db.add_event(con, "window", title=title, body=cls,
                                 meta=json.dumps({"class": cls}))
                since = 0.0
            time.sleep(interval)
    except KeyboardInterrupt:
        pass
