from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path

from prestes_os.services.config_service import ConfigService
from prestes_os.services.event_bus import EventBus


@dataclass
class SyncItem:
    """Responsabilidade: representar um arquivo preparado para sincronizacao."""

    category: str
    path: Path
    relative_path: str
    size_bytes: int
    sha256: str


@dataclass
class SyncManifest:
    """Responsabilidade: representar o manifesto gerado para sincronizacao."""

    provider: str
    generated_at: str
    manifest_file: Path
    items: list[SyncItem]


class SyncService:
    """Responsabilidade: preparar o conjunto de arquivos para sincronizacao futura."""

    def __init__(self, config_service: ConfigService | None = None, event_bus: EventBus | None = None):
        self.config = config_service or ConfigService()
        self.bus = event_bus or EventBus()

    def _base_dir(self) -> Path:
        return Path(self.config.get("base_dir")).expanduser()

    def _manifest_dir(self) -> Path:
        return Path(self.config.get("sync.manifest_dir")).expanduser()

    def _transcriptions_dir(self) -> Path:
        return Path(self.config.get("audio.transcricoes_dir")).expanduser()

    def _summaries_dir(self) -> Path:
        return Path(self.config.get("ai.resumos_dir")).expanduser()

    def _logs_path(self) -> Path:
        return Path(self.config.get("logs.path")).expanduser()

    def _hash_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _collect_files(self) -> list[tuple[str, Path]]:
        collected = []
        transcriptions_dir = self._transcriptions_dir()
        summaries_dir = self._summaries_dir()

        if transcriptions_dir.exists():
            collected.extend(("transcription", path) for path in transcriptions_dir.rglob("*.txt"))
            collected.extend(("transcription", path) for path in transcriptions_dir.rglob("*.json"))
            collected.extend(("transcription", path) for path in transcriptions_dir.rglob("*.srt"))

        if summaries_dir.exists():
            collected.extend(("summary", path) for path in summaries_dir.rglob("*.txt"))

        if self.config.get("sync.include_logs", False):
            logs_path = self._logs_path()
            if logs_path.exists():
                collected.append(("log", logs_path))

        unique = {}
        for category, path in collected:
            unique[str(path)] = (category, path)
        return [unique[key] for key in sorted(unique.keys())]

    def build_manifest(self) -> SyncManifest:
        provider = self.config.get("sync.provider", "local-manifest")
        manifest_dir = self._manifest_dir()
        manifest_dir.mkdir(parents=True, exist_ok=True)

        items = []
        for category, path in self._collect_files():
            items.append(
                SyncItem(
                    category=category,
                    path=path,
                    relative_path=str(path.relative_to(self._base_dir())),
                    size_bytes=path.stat().st_size,
                    sha256=self._hash_file(path),
                )
            )

        manifest_file = manifest_dir / "sync_manifest.json"
        payload = {
            "provider": provider,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "items": [
                {
                    "category": item.category,
                    "path": str(item.path),
                    "relative_path": item.relative_path,
                    "size_bytes": item.size_bytes,
                    "sha256": item.sha256,
                }
                for item in items
            ],
        }
        manifest_file.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

        self.bus.publish(
            "sync.manifest.generated",
            "sync",
            str(manifest_file),
            payload={"provider": provider, "quantidade": len(items)},
        )

        return SyncManifest(
            provider=provider,
            generated_at=payload["generated_at"],
            manifest_file=manifest_file,
            items=items,
        )
