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

    assert data["sync"]["provider"] == "local-manifest"
    assert Path(data["sync"]["manifest_dir"]) == prestes_base_dir / "Sync"
    assert data["sync"]["include_logs"] is False
