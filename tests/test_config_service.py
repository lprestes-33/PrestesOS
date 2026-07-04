from pathlib import Path

from prestes_os.services.config_service import ConfigService


def test_config_service_creates_default_config(prestes_base_dir):
    config = ConfigService(base_dir=prestes_base_dir)

    data = config.load()

    assert Path(data["base_dir"]) == prestes_base_dir
    assert Path(data["audio"]["gravacoes_dir"]) == prestes_base_dir / "Gravacoes"
    assert Path(data["database"]["path"]) == prestes_base_dir / "database" / "prestes.db"


def test_config_service_merges_missing_keys(prestes_base_dir):
    config_path = prestes_base_dir / "config" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("audio:\n  idioma: en\n", encoding="utf-8")

    config = ConfigService(base_dir=prestes_base_dir, config_path=config_path)
    data = config.load()

    assert data["audio"]["idioma"] == "en"
    assert Path(data["audio"]["gravacoes_dir"]) == prestes_base_dir / "Gravacoes"
    assert Path(data["logs"]["path"]) == prestes_base_dir / "logs" / "prestes.log"


def test_config_service_replaces_invalid_critical_values(prestes_base_dir):
    config = ConfigService(base_dir=prestes_base_dir)
    config.save(
        {
            "audio": {
                "duracao_parte_minutos": 0,
                "comando_whisper": "",
                "idioma": "",
            }
        }
    )

    data = config.load()

    assert data["audio"]["duracao_parte_minutos"] == 30
    assert data["audio"]["comando_whisper"] == "whisper-cli"
    assert data["audio"]["idioma"] == "pt"


def test_config_service_keeps_sync_defaults(prestes_base_dir):
    config = ConfigService(base_dir=prestes_base_dir)

    data = config.load()

    assert data["gmail"]["provider"] == "gmail-api-preparado"
    assert Path(data["gmail"]["credentials_path"]) == prestes_base_dir / "config" / "gmail_credentials.json"
    assert data["gmail"]["access_token_env"] == "GMAIL_ACCESS_TOKEN"
    assert data["gmail"]["credentials_access_token_key"] == "access_token"
    assert data["gmail"]["credentials_expires_at_key"] == "expires_at"
    assert data["gmail"]["default_query"] == "label:inbox newer_than:7d"
    assert data["gmail"]["max_results"] == 20
    assert data["sync"]["provider"] == "local-manifest"
    assert Path(data["sync"]["manifest_dir"]) == prestes_base_dir / "Sync"
    assert Path(data["sync"]["state_file"]) == prestes_base_dir / "Sync" / "sync_state.json"
    assert data["sync"]["include_logs"] is False
    assert data["sync"]["google_drive"]["remote_root"] == "PrestesOS"
    assert Path(data["sync"]["google_drive"]["credentials_path"]) == prestes_base_dir / "config" / "google_drive_credentials.json"
    assert Path(data["sync"]["google_drive"]["plan_file"]) == prestes_base_dir / "Sync" / "google_drive_upload_plan.json"
    assert data["sync"]["google_drive"]["access_token_env"] == "GOOGLE_DRIVE_ACCESS_TOKEN"
    assert data["sync"]["google_drive"]["credentials_access_token_key"] == "access_token"
    assert data["sync"]["google_drive"]["credentials_expires_at_key"] == "expires_at"
    assert data["sync"]["google_drive"]["root_folder_id"] == "root"
