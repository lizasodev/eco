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


def test_expanded_filters(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    privacy._custom_rules.cache_clear()
    blocked = [
        "cat ~/.ssh/id_ed25519", "vim .env", "export AWS_SECRET_KEY=abc", "docker login -u me",
        "mysql -u root -phunter2", "nmcli device wifi connect X password Y", "su - root",
        "echo 4111 1111 1111 1111", "pay ES91 2100 0418 4502 0005 1332", "echo 12345678Z",
        "curl https://hooks.slack.com/services/T000/B000/XXXX",
        "echo Zm9vYmFyYmF6cXV4MTIzNDU2Nzg5MGFiY2RlZmdoaWo",
    ]
    for c in blocked:
        assert not privacy.command_allowed(c), c
    for ok in ["git show 3d3c42e5aac5ba805825da76410c181273ba90b1", "ls ~/proyectos/mi-app", "pytest -q",
               "git commit -m 'fix parser'", "echo 4111 1111 1111 1112"]:
        assert privacy.command_allowed(ok), ok
    assert not privacy.window_allowed("firefox", "Tarjeta de crédito - Mi cuenta")
    assert not privacy.window_allowed("kitty", "vim ~/.env")
    assert privacy.window_allowed("kitty", "nvim cli.py")


def test_custom_rules(tmp_path, monkeypatch):
    (tmp_path / "eco").mkdir()
    (tmp_path / "eco" / "privacy.txt").write_text("# mis reglas\ncmd:mi-cliente\nwindow:^Slack\n[roto(\n")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    privacy._custom_rules.cache_clear()
    assert not privacy.command_allowed("cd ~/mi-cliente")
    assert privacy.window_allowed("kitty", "mi-cliente notas")     # regla solo de cmd
    assert not privacy.window_allowed("slack", "Slack | general")
    privacy._custom_rules.cache_clear()
