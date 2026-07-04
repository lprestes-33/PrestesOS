from prestes_os.services.config_service import ConfigService
from prestes_os.services.event_bus import EventBus
from prestes_os.services.platform_service import PlatformService


def test_platform_service_reports_core_ready_with_local_foundations(prestes_base_dir, database_service, log_service):
    config = ConfigService(base_dir=prestes_base_dir)
    config.load()
    log_service.info("diagnostico iniciado")
    database_service.create_recording("Aula", "Teste", prestes_base_dir / "gravacao")
    database_service.create_transcription(1, prestes_base_dir / "Transcricoes" / "teste.txt", "conteudo")
    database_service.upsert_search_document("summary", prestes_base_dir / "Resumos" / "teste.txt", "Resumo", "conteudo")

    bus = EventBus(db_service=database_service, log_service=log_service)
    service = PlatformService(
        config_service=config,
        database_service=database_service,
        event_bus=bus,
        log_service=log_service,
    )

    report = service.status()
    checks = {check.key: check for check in report.checks}

    assert report.target_version == "v1.0"
    assert report.core_ready is True
    assert checks["config"].status == "ok"
    assert checks["database"].details["recordings"] == 1
    assert checks["database"].details["transcriptions"] == 1
    assert checks["database"].details["search_documents"] == 1
    assert checks["logs"].status == "ok"
    assert checks["sync"].details["provider"] == "local-manifest"


def test_platform_service_marks_optional_integrations_as_warning_without_tokens(
    prestes_base_dir,
    database_service,
    log_service,
):
    config = ConfigService(base_dir=prestes_base_dir)
    config.load()

    bus = EventBus(db_service=database_service, log_service=log_service)
    service = PlatformService(
        config_service=config,
        database_service=database_service,
        event_bus=bus,
        log_service=log_service,
    )

    report = service.status()
    checks = {check.key: check for check in report.checks}

    assert checks["google_drive"].status == "warning"
    assert checks["gmail"].status == "warning"
    assert checks["calendar"].status == "warning"
    assert checks["notebooklm"].status == "warning"
