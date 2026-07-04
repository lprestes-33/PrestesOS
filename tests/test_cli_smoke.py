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

    main_module.main([])

    db = database_service.DatabaseService(db_path=prestes_base / "database" / "prestes.db")
    rows = db.last_events(2)

    assert (prestes_base / "database" / "prestes.db").exists()
    assert rows[0][1] == "sistema.encerrado"
    assert rows[1][1] == "sistema.iniciado"


def test_direct_record_command_dispatches_to_audio_service(monkeypatch):
    calls = []

    monkeypatch.setattr(
        main_module,
        "executar_gravacao_direta",
        lambda tipo, titulo: calls.append((tipo, titulo)),
    )

    main_module.main(["gravar", "--tipo", "Conversa", "--titulo", "Revisao"])

    assert calls == [("Conversa", "Revisao")]


def test_direct_transcription_command_dispatches_to_service(monkeypatch):
    calls = []

    monkeypatch.setattr(
        main_module,
        "executar_preparacao_transcricao",
        lambda: calls.append("transcrever"),
    )

    main_module.main(["transcrever"])

    assert calls == ["transcrever"]


def test_direct_ai_command_dispatches_to_service(monkeypatch):
    calls = []

    monkeypatch.setattr(
        main_module,
        "executar_resumo_ia",
        lambda tipo=None: calls.append(tipo),
    )

    main_module.main(["resumir", "--tipo", "Aula"])

    assert calls == ["Aula"]


def test_direct_search_command_dispatches_to_service(monkeypatch):
    calls = []

    monkeypatch.setattr(
        main_module,
        "executar_busca_textual",
        lambda consulta: calls.append(consulta),
    )

    main_module.main(["buscar", "competencia"])

    assert calls == ["competencia"]


def test_direct_semantic_search_command_dispatches_to_service(monkeypatch):
    calls = []

    monkeypatch.setattr(
        main_module,
        "executar_busca_semantica",
        lambda consulta: calls.append(consulta),
    )

    main_module.main(["buscar-semantico", "jurisdicao"])

    assert calls == ["jurisdicao"]


def test_direct_sync_command_dispatches_to_service(monkeypatch):
    calls = []

    monkeypatch.setattr(
        main_module,
        "executar_preparacao_sync",
        lambda: calls.append("sync"),
    )

    main_module.main(["sincronizar"])

    assert calls == ["sync"]


def test_direct_sync_history_command_dispatches_to_service(monkeypatch):
    calls = []

    monkeypatch.setattr(
        main_module,
        "executar_historico_sync",
        lambda: calls.append("history"),
    )

    main_module.main(["historico-sync"])

    assert calls == ["history"]
