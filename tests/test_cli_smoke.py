from prestes_os.core import main as main_module
from prestes_os.services import config_service, database_service, log_service


def test_main_starts_and_exits_cleanly(monkeypatch, tmp_path):
    base_home = tmp_path
    prestes_base = base_home / "PrestesOS"

    monkeypatch.setattr(config_service, "default_base_dir", lambda: prestes_base)
    monkeypatch.setattr(
        database_service,
        "default_db_path",
        lambda: prestes_base / "database" / "prestes.db",
    )
    monkeypatch.setattr(
        log_service,
        "default_log_file",
        lambda: prestes_base / "logs" / "prestes.log",
    )
    monkeypatch.setattr(main_module.console, "clear", lambda: None)
    monkeypatch.setattr(main_module.console, "print", lambda *args, **kwargs: None)
    monkeypatch.setattr(main_module.console, "input", lambda *args, **kwargs: "0")

    main_module.main()

    db = database_service.DatabaseService(db_path=prestes_base / "database" / "prestes.db")
    rows = db.last_events(2)

    assert (prestes_base / "database" / "prestes.db").exists()
    assert rows[0][1] == "sistema.encerrado"
    assert rows[1][1] == "sistema.iniciado"
