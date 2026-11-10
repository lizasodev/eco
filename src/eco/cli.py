import argparse
import json
import re
import sys
import time
from datetime import datetime

from . import db, hooks, privacy

UNITS = {"m": 60, "h": 3600, "d": 86400, "w": 604800}


def parse_since(s):
    m = re.fullmatch(r"(\d+)([mhdw])", s or "")
    if not m:
        sys.exit("formato inválido; usa p. ej. 30m, 2h, 7d, 2w")
    return time.time() - int(m[1]) * UNITS[m[2]]


def fmt_ts(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def show(r, score=False):
    icon = {"cmd": "$", "window": "▣"}.get(r["kind"], "?")
    meta = json.loads(r["meta"] or "{}")
    if r["kind"] == "cmd":
        extra = f"  [{meta.get('cwd','')}]" + (f" exit={meta['exit']}" if meta.get("exit") not in (None, 0) else "")
        line = f"{r['title']}{extra}"
    else:
        line = f"{r['title']}  ({r['body']})"
    print(f"#{r['id']:<6} {fmt_ts(r['ts'])} {icon} {line}")


def cmd_record(a):
    text = " ".join(a.text).strip()
    if not text or not privacy.command_allowed(text):
        return
    con = db.connect()
    db.add_event(con, "cmd", title=text, meta=json.dumps({"cwd": a.cwd, "exit": a.exit}))


def cmd_search(a):
    con = db.connect()
    rows = db.search(con, " ".join(a.query), a.kind, parse_since(a.since) if a.since else None, a.limit)
    if not rows:
        print("Sin resultados.")
    for r in rows:
        show(r)
    if rows:
        print("\nTip: `eco around <id>` muestra qué pasaba antes y después.")


def cmd_around(a):
    con = db.connect()
    row = con.execute("SELECT * FROM events WHERE id=?", (a.id,)).fetchone()
    if not row:
        sys.exit("evento no encontrado")
    for r in db.around(con, row["ts"], a.minutes):
        print("→ " if r["id"] == row["id"] else "  ", end="")
        show(r)


def cmd_timeline(a):
    con = db.connect()
    for r in reversed(db.recent(con, parse_since(a.since), a.kind, a.limit)):
        show(r)


def cmd_stats(a):
    con = db.connect()
    for r in con.execute("SELECT kind, COUNT(*) n, MIN(ts) a, MAX(ts) b FROM events GROUP BY kind"):
        print(f"{r['kind']:<8} {r['n']:>7} eventos  ({fmt_ts(r['a'])} → {fmt_ts(r['b'])})")
    print(f"DB: {db.db_path()}")


def cmd_purge(a):
    con = db.connect()
    n = db.purge(con, parse_since(a.older_than))
    print(f"{n} eventos borrados.")


def cmd_forget(a):
    q = db._fts_query(" ".join(a.query))
    if not q:
        sys.exit("consulta vacía: nada que olvidar")
    con = db.connect()
    n = con.execute("DELETE FROM events WHERE id IN (SELECT rowid FROM events_fts WHERE events_fts MATCH ?)",
                    (q,)).rowcount
    con.commit()
    print(f"{n} eventos olvidados.")


def cmd_hook(a):
    print(hooks.BASH if a.shell == "bash" else hooks.ZSH)


def cmd_daemon(a):
    from . import daemon
    daemon.run(a.interval)


def main(argv=None):
    p = argparse.ArgumentParser(prog="eco", description="Tu segundo cerebro local.")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("record", help="(interno) registra un evento"); s.set_defaults(f=cmd_record)
    s.add_argument("kind", choices=["cmd"]); s.add_argument("--cwd", default=""); s.add_argument("--exit", type=int, default=0)
    s.add_argument("text", nargs="+")

    s = sub.add_parser("search", aliases=["s"], help="busca en tu pasado"); s.set_defaults(f=cmd_search)
    s.add_argument("query", nargs="+"); s.add_argument("--kind", choices=["cmd", "window"])
    s.add_argument("--since", help="p. ej. 2d, 1w"); s.add_argument("-n", "--limit", type=int, default=20)

    s = sub.add_parser("around", help="línea de tiempo alrededor de un evento"); s.set_defaults(f=cmd_around)
    s.add_argument("id", type=int); s.add_argument("-m", "--minutes", type=int, default=15)

    s = sub.add_parser("timeline", help="actividad reciente"); s.set_defaults(f=cmd_timeline)
    s.add_argument("--since", default="2h"); s.add_argument("--kind", choices=["cmd", "window"])
    s.add_argument("-n", "--limit", type=int, default=100)

    sub.add_parser("stats", help="resumen de la base de datos").set_defaults(f=cmd_stats)

    s = sub.add_parser("purge", help="borra eventos antiguos"); s.set_defaults(f=cmd_purge)
    s.add_argument("--older-than", required=True, help="p. ej. 90d")

    s = sub.add_parser("forget", help="borra todo lo que coincida con una búsqueda"); s.set_defaults(f=cmd_forget)
    s.add_argument("query", nargs="+")

    s = sub.add_parser("hook", help="imprime el hook de shell"); s.set_defaults(f=cmd_hook)
    s.add_argument("shell", choices=["bash", "zsh"])

    s = sub.add_parser("daemon", help="observa la ventana activa (Hyprland)"); s.set_defaults(f=cmd_daemon)
    s.add_argument("--interval", type=float, default=2.0)

    a = p.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()
