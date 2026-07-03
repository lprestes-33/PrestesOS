from pathlib import Path

from prestes_os.services.config_service import ConfigService
from prestes_os.services.event_bus import EventBus
from prestes_os.services.sync_service import SyncService


def create_sync_fixture(prestes_base_dir: Path):
    transcription_folder = prestes_base_dir / "Transcricoes" / "03072026" / "aula-processo"
    transcription_folder.mkdir(parents=True, exist_ok=True)
    (transcription_folder / "TRANSCRICAO_COMPLETA.txt").write_text("transcricao", encoding="utf-8")
    (transcription_folder / "parte01.json").write_text('{"text":"oi"}', encoding="utf-8")

    summary_folder = prestes_base_dir / "Resumos" / "03072026" / "aula-processo"
    summary_folder.mkdir(parents=True, exist_ok=True)
    (summary_folder / "RESUMO_AULA.txt").write_text("resumo", encoding="utf-8")


def test_sync_service_builds_manifest(prestes_base_dir, database_service, log_service):
    create_sync_fixture(prestes_base_dir)
    config = ConfigService(base_dir=prestes_base_dir)
    bus = EventBus(db_service=database_service, log_service=log_service)
    service = SyncService(config_service=config, event_bus=bus)

    result = service.build_manifest()

    assert result.manifest_file.exists()
    assert len(result.items) == 3
    assert any(item.relative_path.endswith("TRANSCRICAO_COMPLETA.txt") for item in result.items)


def test_sync_service_includes_logs_when_enabled(prestes_base_dir, database_service, log_service):
    create_sync_fixture(prestes_base_dir)
    log_service.info("teste sync")
    config = ConfigService(base_dir=prestes_base_dir)
    data = config.load()
    data["sync"]["include_logs"] = True
    config.save(data)
    bus = EventBus(db_service=database_service, log_service=log_service)
    service = SyncService(config_service=config, event_bus=bus)

    result = service.build_manifest()

    assert any(item.category == "log" for item in result.items)


def test_sync_service_builds_google_drive_plan(prestes_base_dir, database_service, log_service):
    create_sync_fixture(prestes_base_dir)
    credentials_path = prestes_base_dir / "config" / "google_drive_credentials.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text('{"installed":{}}', encoding="utf-8")

    config = ConfigService(base_dir=prestes_base_dir)
    data = config.load()
    data["sync"]["provider"] = "google-drive"
    config.save(data)

    bus = EventBus(db_service=database_service, log_service=log_service)
    service = SyncService(config_service=config, event_bus=bus)

    result = service.prepare_sync()

    assert result.upload_plan is not None
    assert result.upload_plan.plan_file.exists()
    assert result.upload_plan.credentials_configured is True
    assert result.upload_plan.remote_root == "PrestesOS"
    assert all(plan_item.remote_path.startswith("PrestesOS/") for plan_item in result.upload_plan.items)


def test_sync_service_google_drive_plan_marks_missing_credentials(prestes_base_dir, database_service, log_service):
    create_sync_fixture(prestes_base_dir)
    config = ConfigService(base_dir=prestes_base_dir)
    data = config.load()
    data["sync"]["provider"] = "google-drive"
    config.save(data)

    bus = EventBus(db_service=database_service, log_service=log_service)
    service = SyncService(config_service=config, event_bus=bus)

    result = service.prepare_sync()

    assert result.upload_plan is not None
    assert result.upload_plan.credentials_configured is False
