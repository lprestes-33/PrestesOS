from pathlib import Path

import yaml


def default_base_dir() -> Path:
    return Path.home() / "PrestesOS"


def build_default_config(base_dir: Path | None = None) -> dict:
    base = Path(base_dir) if base_dir is not None else default_base_dir()
    return {
        "base_dir": str(base),
        "audio": {
            "gravacoes_dir": str(base / "Gravacoes"),
            "transcricoes_dir": str(base / "Transcricoes"),
            "modelo_whisper": str(Path.home() / "whisper.cpp/models/ggml-small.bin"),
            "idioma": "pt",
            "duracao_parte_minutos": 30,
        },
        "database": {
            "path": str(base / "database" / "prestes.db"),
        },
        "logs": {
            "path": str(base / "logs" / "prestes.log"),
        },
    }


class ConfigService:
    """Responsabilidade: persistir e expor a configuracao central do PrestesOS."""

    def __init__(self, config_path: Path | None = None, base_dir: Path | None = None):
        self.base_dir = Path(base_dir) if base_dir is not None else default_base_dir()
        self.config_path = (
            Path(config_path)
            if config_path is not None
            else self.base_dir / "config" / "config.yaml"
        )
        self.default_config = build_default_config(self.base_dir)

        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.config_path.exists():
            self.save(self.default_config)

    def load(self):
        with self.config_path.open("r", encoding="utf-8") as file_handle:
            return yaml.safe_load(file_handle)

    def save(self, data):
        with self.config_path.open("w", encoding="utf-8") as file_handle:
            yaml.safe_dump(data, file_handle, allow_unicode=True, sort_keys=False)

    def get(self, key, default=None):
        data = self.load()
        current = data
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current
