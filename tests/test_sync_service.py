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
    assert result.upload_plan.skipped_items == []


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


def test_sync_service_execute_sync_marks_pending_auth(monkeypatch, prestes_base_dir, database_service, log_service):
    create_sync_fixture(prestes_base_dir)
    config = ConfigService(base_dir=prestes_base_dir)
    data = config.load()
    data["sync"]["provider"] = "google-drive"
    config.save(data)

    monkeypatch.delenv("GOOGLE_DRIVE_ACCESS_TOKEN", raising=False)

    bus = EventBus(db_service=database_service, log_service=log_service)
    service = SyncService(config_service=config, event_bus=bus)

    result = service.execute_sync()

    assert result.preparation.upload_plan is not None
    assert result.upload_result is None


def test_sync_service_execute_sync_uploads_to_google_drive(monkeypatch, prestes_base_dir, database_service, log_service):
    class FakeGoogleDriveClient:
        def __init__(self):
            self.ensure_calls = []
            self.upload_calls = []

        def ensure_folder_path(self, folder_parts):
            self.ensure_calls.append(tuple(folder_parts))
            return "folder-123"

        def upload_file(self, parent_id, file_name, local_path):
            self.upload_calls.append((parent_id, file_name, local_path))
            return "uploaded", f"id-{file_name}"

    create_sync_fixture(prestes_base_dir)
    config = ConfigService(base_dir=prestes_base_dir)
    data = config.load()
    data["sync"]["provider"] = "google-drive"
    config.save(data)

    monkeypatch.setenv("GOOGLE_DRIVE_ACCESS_TOKEN", "token-teste")

    bus = EventBus(db_service=database_service, log_service=log_service)
    service = SyncService(config_service=config, event_bus=bus)
    fake_client = FakeGoogleDriveClient()
    monkeypatch.setattr(service, "_build_google_drive_client", lambda: fake_client)

    result = service.execute_sync()

    assert result.upload_result is not None
    assert result.upload_result.uploaded_count == 3
    assert result.upload_result.skipped_count == 0
    assert len(fake_client.upload_calls) == 3


def test_sync_service_skips_already_synced_files(monkeypatch, prestes_base_dir, database_service, log_service):
    class FakeGoogleDriveClient:
        def __init__(self):
            self.upload_calls = []

        def ensure_folder_path(self, folder_parts):
            return "folder-123"

        def upload_file(self, parent_id, file_name, local_path):
            self.upload_calls.append((parent_id, file_name, local_path))
            return "uploaded", f"id-{file_name}"

    create_sync_fixture(prestes_base_dir)
    config = ConfigService(base_dir=prestes_base_dir)
    data = config.load()
    data["sync"]["provider"] = "google-drive"
    config.save(data)

    monkeypatch.setenv("GOOGLE_DRIVE_ACCESS_TOKEN", "token-teste")

    bus = EventBus(db_service=database_service, log_service=log_service)
    service = SyncService(config_service=config, event_bus=bus)
    fake_client = FakeGoogleDriveClient()
    monkeypatch.setattr(service, "_build_google_drive_client", lambda: fake_client)

    first_result = service.execute_sync()
    second_result = service.execute_sync()

    assert first_result.upload_result is not None
    assert second_result.preparation.upload_plan is not None
    assert second_result.upload_result is not None
    assert second_result.upload_result.uploaded_count == 0
    assert second_result.upload_result.skipped_count == 3
    assert len(second_result.preparation.upload_plan.skipped_items) == 3
    assert len(fake_client.upload_calls) == 3
