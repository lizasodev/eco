import time
from eco import db, privacy


def test_search_and_around(tmp_path, monkeypatch):
    monkeypatch.setenv("ECO_DB", str(tmp_path / "t.db"))
    con = db.connect()
    now = time.time()
    db.add_event(con, "cmd", title="bluetoothctl connect AA:BB", ts=now - 100)
    db.add_event(con, "window", title="Arch Wiki - Bluetooth", body="firefox", ts=now - 50)
    db.add_event(con, "cmd", title="ls -la", ts=now - 10)
    assert [r["kind"] for r in db.search(con, "bluetooth")] == ["cmd", "window"] or len(db.search(con, "bluetooth")) == 2
    assert len(db.search(con, "blueto")) == 2          # prefijo
    assert len(db.search(con, "bluetooth", kind="cmd")) == 1
    assert len(db.around(con, now - 50, minutes=1)) == 3
    assert db.purge(con, now - 30) == 2
    assert db.search(con, "bluetooth") == []           # FTS sincronizado tras borrar


def test_query_sanitized(tmp_path, monkeypatch):
    monkeypatch.setenv("ECO_DB", str(tmp_path / "t.db"))
    con = db.connect()
    db.search(con, 'foo" OR (bar')                     # no debe lanzar


def test_privacy():
    assert not privacy.command_allowed("export TOKEN=abc")
    assert privacy.command_allowed("git status")
    assert not privacy.window_allowed("firefox", "Mi Banco - Login")
    assert not privacy.window_allowed("keepassxc", "x")
    assert privacy.window_allowed("kitty", "nvim main.py")


def test_permissions_and_secrets(tmp_path, monkeypatch):
    import os, stat
    monkeypatch.setenv("ECO_DB", str(tmp_path / "p.db"))
    con = db.connect()
    db.add_event(con, "cmd", title="echo hi")
    assert stat.S_IMODE(os.stat(tmp_path / "p.db").st_mode) == 0o600
    for bad in ["curl -u bob:pw https://x", "git clone https://u:p@h/r.git", "sudo ls",
                "echo ghp_" + "a" * 30, "export OPENAI=sk-" + "b" * 30]:
        assert not privacy.command_allowed(bad), bad
    assert privacy.command_allowed("git commit -m 'fix'")


def test_empty_query(tmp_path, monkeypatch):
    monkeypatch.setenv("ECO_DB", str(tmp_path / "e.db"))
    con = db.connect()
    assert db.search(con, "   ") == [] and db.search(con, '"*') == []
