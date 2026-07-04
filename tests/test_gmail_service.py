from pathlib import Path

from prestes_os.services.config_service import ConfigService
from prestes_os.services.event_bus import EventBus
from prestes_os.services.gmail_service import GmailService


def test_gmail_service_resolves_auth_from_env(prestes_base_dir, database_service, log_service):
    config = ConfigService(base_dir=prestes_base_dir)
    bus = EventBus(db_service=database_service, log_service=log_service)
    service = GmailService(
        config_service=config,
        event_bus=bus,
        environment={"GMAIL_ACCESS_TOKEN": "env-token"},
    )

    auth = service.resolve_auth()

    assert auth.source == "env"
    assert auth.access_token == "env-token"


def test_gmail_service_resolves_auth_from_file(prestes_base_dir, database_service, log_service):
    credentials_path = prestes_base_dir / "config" / "gmail_credentials.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text('{"access_token":"file-token"}', encoding="utf-8")

    config = ConfigService(base_dir=prestes_base_dir)
    bus = EventBus(db_service=database_service, log_service=log_service)
    service = GmailService(config_service=config, event_bus=bus, environment={})

    auth = service.resolve_auth()

    assert auth.source == "file"
    assert auth.access_token == "file-token"


def test_gmail_service_marks_expired_file_token(prestes_base_dir, database_service, log_service):
    credentials_path = prestes_base_dir / "config" / "gmail_credentials.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        '{"access_token":"file-token","expires_at":"2000-01-01T00:00:00+00:00"}',
        encoding="utf-8",
    )

    config = ConfigService(base_dir=prestes_base_dir)
    bus = EventBus(db_service=database_service, log_service=log_service)
    service = GmailService(config_service=config, event_bus=bus, environment={})

    auth = service.resolve_auth()

    assert auth.source == "file-expired"
    assert auth.access_token is None
    assert auth.is_expired is True


def test_gmail_service_returns_status(prestes_base_dir, database_service, log_service):
    config = ConfigService(base_dir=prestes_base_dir)
    bus = EventBus(db_service=database_service, log_service=log_service)
    service = GmailService(
        config_service=config,
        event_bus=bus,
        environment={"GMAIL_ACCESS_TOKEN": "env-token"},
    )

    status = service.status()

    assert status.provider == "gmail-api-preparado"
    assert status.auth.source == "env"
    assert status.default_query == "label:inbox newer_than:7d"
    assert status.max_results == 20
