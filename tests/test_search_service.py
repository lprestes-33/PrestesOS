from pathlib import Path

from prestes_os.services.config_service import ConfigService
from prestes_os.services.event_bus import EventBus
from prestes_os.services.search_service import SearchService


def create_search_fixture(prestes_base_dir: Path):
    transcription_folder = prestes_base_dir / "Transcricoes" / "03072026" / "aula-processo"
    transcription_folder.mkdir(parents=True, exist_ok=True)
    (transcription_folder / "TRANSCRICAO_COMPLETA.txt").write_text(
        "Competencia e processo civil aparecem neste material de estudo.",
        encoding="utf-8",
    )

    summary_folder = prestes_base_dir / "Resumos" / "03072026" / "aula-processo"
    summary_folder.mkdir(parents=True, exist_ok=True)
    (summary_folder / "RESUMO_AULA.txt").write_text(
        "Resumo de Aula com foco em competencia, jurisdicao e processo.",
        encoding="utf-8",
    )


def test_search_service_reindexes_documents(prestes_base_dir, database_service, log_service):
    create_search_fixture(prestes_base_dir)
    config = ConfigService(base_dir=prestes_base_dir)
    bus = EventBus(db_service=database_service, log_service=log_service)
    service = SearchService(config_service=config, database_service=database_service, event_bus=bus)

    indexed = service.reindex_documents()

    rows = database_service.search_documents("processo", limit=10)
    assert indexed == 2
    assert len(rows) == 2


def test_search_service_returns_matching_results(prestes_base_dir, database_service, log_service):
    create_search_fixture(prestes_base_dir)
    config = ConfigService(base_dir=prestes_base_dir)
    bus = EventBus(db_service=database_service, log_service=log_service)
    service = SearchService(config_service=config, database_service=database_service, event_bus=bus)
    service.reindex_documents()

    results = service.search("competencia")

    assert len(results) == 2
    assert any("competencia" in result.snippet.lower() for result in results)
    assert any(result.source_type == "summary" for result in results)


def test_search_service_rejects_empty_query(prestes_base_dir, database_service, log_service):
    config = ConfigService(base_dir=prestes_base_dir)
    bus = EventBus(db_service=database_service, log_service=log_service)
    service = SearchService(config_service=config, database_service=database_service, event_bus=bus)

    try:
        service.search("   ")
    except ValueError as exc:
        assert "termo nao vazio" in str(exc)
    else:
        raise AssertionError("Era esperado falhar com consulta vazia.")
