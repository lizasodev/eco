import os
import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id    INTEGER PRIMARY KEY,
    ts    REAL NOT NULL,
    kind  TEXT NOT NULL,          -- cmd | window
    title TEXT NOT NULL DEFAULT '',
    body  TEXT NOT NULL DEFAULT '',
    meta  TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS events_ts ON events(ts);
CREATE VIRTUAL TABLE IF NOT EXISTS events_fts USING fts5(
    title, body, content='events', content_rowid='id', tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS events_ai AFTER INSERT ON events BEGIN
    INSERT INTO events_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
END;
CREATE TRIGGER IF NOT EXISTS events_ad AFTER DELETE ON events BEGIN
    INSERT INTO events_fts(events_fts, rowid, title, body) VALUES ('delete', old.id, old.title, old.body);
END;
"""


def db_path() -> Path:
    base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "eco"
    base.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        os.chmod(base, 0o700)
    except OSError:
        pass
    return Path(os.environ.get("ECO_DB", base / "eco.db"))


def _secure_files(path: Path) -> None:
    """La DB contiene tu actividad: solo legible por tu usuario (0600), incluidos -wal/-shm."""
    for suffix in ("", "-wal", "-shm"):
        f = Path(str(path) + suffix)
        if f.exists():
            try:
                os.chmod(f, 0o600)
            except OSError:
                pass


def connect() -> sqlite3.Connection:
    old_umask = os.umask(0o077)  # cualquier fichero nuevo nace privado
    try:
        return _connect()
    finally:
        os.umask(old_umask)


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(db_path(), timeout=30)
    con.row_factory = sqlite3.Row
    # El DDL solo se ejecuta una vez: evita carreras entre procesos concurrentes.
    if con.execute("PRAGMA user_version").fetchone()[0] < 1:
        con.execute("PRAGMA journal_mode=WAL")
        con.executescript(SCHEMA)
        con.execute("PRAGMA user_version=1")
    con.execute("PRAGMA secure_delete=ON")  # los borrados sobrescriben el contenido
    _secure_files(db_path())
    return con


MAX_FIELD = 4000  # recorta entradas absurdamente largas


def add_event(con, kind, title="", body="", meta="{}", ts=None):
    title, body = title[:MAX_FIELD], body[:MAX_FIELD]
    con.execute(
        "INSERT INTO events(ts, kind, title, body, meta) VALUES (?,?,?,?,?)",
        (ts or time.time(), kind, title, body, meta),
    )
    con.commit()


def _fts_query(q: str) -> str:
    # Cada palabra como prefijo, unidas con AND; evita errores de sintaxis FTS.
    terms = ["".join(c for c in t if c.isalnum() or c in "_-") for t in q.split()]
    return " ".join(f'"{t}"*' for t in terms if t)


def search(con, q, kind=None, since=None, limit=20):
    sql = ("SELECT e.*, bm25(events_fts, 3.0, 1.0) AS score FROM events_fts "
           "JOIN events e ON e.id = events_fts.rowid WHERE events_fts MATCH ?")
    fq = _fts_query(q)
    if not fq:
        return []
    args = [fq]
    if kind:
        sql += " AND e.kind = ?"; args.append(kind)
    if since:
        sql += " AND e.ts >= ?"; args.append(since)
    sql += " ORDER BY score LIMIT ?"; args.append(limit)
    return con.execute(sql, args).fetchall()


def around(con, ts, minutes=15, limit=200):
    d = minutes * 60
    return con.execute(
        "SELECT * FROM events WHERE ts BETWEEN ? AND ? ORDER BY ts LIMIT ?",
        (ts - d, ts + d, limit),
    ).fetchall()


def recent(con, since, kind=None, limit=100):
    sql = "SELECT * FROM events WHERE ts >= ?"
    args = [since]
    if kind:
        sql += " AND kind = ?"; args.append(kind)
    sql += " ORDER BY ts DESC LIMIT ?"; args.append(limit)
    return con.execute(sql, args).fetchall()


def purge(con, before_ts):
    n = con.execute("DELETE FROM events WHERE ts < ?", (before_ts,)).rowcount
    con.commit()
    con.execute("VACUUM")
    return n
