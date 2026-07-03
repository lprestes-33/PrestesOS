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
            "comando_whisper": "whisper-cli",
            "idioma": "pt",
            "duracao_parte_minutos": 30,
        },
        "database": {
            "path": str(base / "database" / "prestes.db"),
        },
        "logs": {
            "path": str(base / "logs" / "prestes.log"),
        },
        "ai": {
            "mode": "offline",
            "provider": "local-placeholder",
            "openai_model": "gpt-4.1-mini",
            "resumos_dir": str(base / "Resumos"),
        },
        "sync": {
            "provider": "local-manifest",
            "manifest_dir": str(base / "Sync"),
            "include_logs": False,
            "google_drive": {
                "remote_root": "PrestesOS",
                "credentials_path": str(base / "config" / "google_drive_credentials.json"),
                "plan_file": str(base / "Sync" / "google_drive_upload_plan.json"),
                "access_token_env": "GOOGLE_DRIVE_ACCESS_TOKEN",
                "root_folder_id": "root",
            },
        },
    }


def merge_dicts(defaults: dict, data: dict | None) -> dict:
    merged = {}
    source = data if isinstance(data, dict) else {}
    for key, default_value in defaults.items():
        source_value = source.get(key)
        if isinstance(default_value, dict):
            merged[key] = merge_dicts(default_value, source_value)
        elif source_value is None:
            merged[key] = default_value
        else:
            merged[key] = source_value
    for key, value in source.items():
        if key not in merged:
            merged[key] = value
    return merged


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

    def _normalize_paths(self, data: dict) -> dict:
        base_dir = Path(data.get("base_dir", self.base_dir)).expanduser()
        data["base_dir"] = str(base_dir)

        for section, key in (
            ("audio", "gravacoes_dir"),
            ("audio", "transcricoes_dir"),
            ("audio", "modelo_whisper"),
            ("database", "path"),
            ("logs", "path"),
            ("ai", "resumos_dir"),
            ("sync", "manifest_dir"),
            ("sync.google_drive", "credentials_path"),
            ("sync.google_drive", "plan_file"),
        ):
            if "." in section:
                top_level, nested = section.split(".", maxsplit=1)
                section_data = data.get(top_level, {}).get(nested, {})
            else:
                section_data = data.get(section, {})
            if key in section_data:
                section_data[key] = str(Path(section_data[key]).expanduser())
        return data

    def _validate(self, data: dict) -> dict:
        audio = data["audio"]
        duration = audio.get("duracao_parte_minutos", 30)
        if not isinstance(duration, int) or duration <= 0:
            audio["duracao_parte_minutos"] = self.default_config["audio"]["duracao_parte_minutos"]

        command = audio.get("comando_whisper")
        if not isinstance(command, str) or not command.strip():
            audio["comando_whisper"] = self.default_config["audio"]["comando_whisper"]

        language = audio.get("idioma")
        if not isinstance(language, str) or not language.strip():
            audio["idioma"] = self.default_config["audio"]["idioma"]

        ai = data["ai"]
        mode = ai.get("mode")
        if mode not in {"offline", "openai"}:
            ai["mode"] = self.default_config["ai"]["mode"]

        provider = ai.get("provider")
        if not isinstance(provider, str) or not provider.strip():
            ai["provider"] = self.default_config["ai"]["provider"]

        model = ai.get("openai_model")
        if not isinstance(model, str) or not model.strip():
            ai["openai_model"] = self.default_config["ai"]["openai_model"]

        sync = data["sync"]
        provider = sync.get("provider")
        if provider not in {"local-manifest", "google-drive"}:
            sync["provider"] = self.default_config["sync"]["provider"]

        include_logs = sync.get("include_logs")
        if not isinstance(include_logs, bool):
            sync["include_logs"] = self.default_config["sync"]["include_logs"]

        google_drive = sync["google_drive"]
        remote_root = google_drive.get("remote_root")
        if not isinstance(remote_root, str) or not remote_root.strip():
            google_drive["remote_root"] = self.default_config["sync"]["google_drive"]["remote_root"]

        access_token_env = google_drive.get("access_token_env")
        if not isinstance(access_token_env, str) or not access_token_env.strip():
            google_drive["access_token_env"] = self.default_config["sync"]["google_drive"]["access_token_env"]

        root_folder_id = google_drive.get("root_folder_id")
        if not isinstance(root_folder_id, str) or not root_folder_id.strip():
            google_drive["root_folder_id"] = self.default_config["sync"]["google_drive"]["root_folder_id"]

        return data

    def load(self):
        with self.config_path.open("r", encoding="utf-8") as file_handle:
            raw_data = yaml.safe_load(file_handle) or {}

        merged = merge_dicts(self.default_config, raw_data)
        normalized = self._normalize_paths(merged)
        validated = self._validate(normalized)

        if validated != raw_data:
            self.save(validated)

        return validated

    def save(self, data):
        prepared = self._validate(self._normalize_paths(merge_dicts(self.default_config, data)))
        with self.config_path.open("w", encoding="utf-8") as file_handle:
            yaml.safe_dump(prepared, file_handle, allow_unicode=True, sort_keys=False)

    def get(self, key, default=None):
        data = self.load()
        current = data
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current
