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


@dataclass
class SyncPlanItem:
    """Responsabilidade: representar um item preparado para destino remoto."""

    category: str
    local_path: Path
    remote_path: str
    size_bytes: int
    sha256: str


@dataclass
class SyncUploadPlan:
    """Responsabilidade: representar um plano de upload por provedor."""

    provider: str
    generated_at: str
    plan_file: Path
    remote_root: str
    credentials_path: Path
    credentials_configured: bool
    items: list[SyncPlanItem]


@dataclass
class SyncPreparation:
    """Responsabilidade: agrupar manifesto local e plano remoto opcional."""

    manifest: SyncManifest
    upload_plan: SyncUploadPlan | None


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

    def _provider(self) -> str:
        return self.config.get("sync.provider", "local-manifest")

    def _google_drive_config(self) -> dict:
        return self.config.get("sync.google_drive", {}) or {}

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
        provider = self._provider()
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

    def _google_drive_remote_path(self, item: SyncItem, remote_root: str) -> str:
        category_root = {
            "transcription": "Transcricoes",
            "summary": "Resumos",
            "log": "Logs",
        }.get(item.category, "Arquivos")
        normalized_relative = item.relative_path.replace("\\", "/")
        return f"{remote_root}/{category_root}/{normalized_relative}"

    def build_google_drive_plan(self, manifest: SyncManifest | None = None) -> SyncUploadPlan:
        current_manifest = manifest or self.build_manifest()
        google_drive = self._google_drive_config()
        remote_root = google_drive.get("remote_root", "PrestesOS").strip("/")
        credentials_path = Path(google_drive.get("credentials_path")).expanduser()
        plan_file = Path(google_drive.get("plan_file")).expanduser()
        plan_file.parent.mkdir(parents=True, exist_ok=True)

        items = [
            SyncPlanItem(
                category=item.category,
                local_path=item.path,
                remote_path=self._google_drive_remote_path(item, remote_root),
                size_bytes=item.size_bytes,
                sha256=item.sha256,
            )
            for item in current_manifest.items
        ]

        payload = {
            "provider": "google-drive",
            "generated_at": current_manifest.generated_at,
            "remote_root": remote_root,
            "credentials_path": str(credentials_path),
            "credentials_configured": credentials_path.exists(),
            "manifest_file": str(current_manifest.manifest_file),
            "items": [
                {
                    "category": item.category,
                    "local_path": str(item.local_path),
                    "remote_path": item.remote_path,
                    "size_bytes": item.size_bytes,
                    "sha256": item.sha256,
                }
                for item in items
            ],
        }
        plan_file.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

        self.bus.publish(
            "sync.google_drive.plan.generated",
            "sync",
            str(plan_file),
            payload={"provider": "google-drive", "quantidade": len(items)},
        )

        return SyncUploadPlan(
            provider="google-drive",
            generated_at=current_manifest.generated_at,
            plan_file=plan_file,
            remote_root=remote_root,
            credentials_path=credentials_path,
            credentials_configured=credentials_path.exists(),
            items=items,
        )

    def prepare_sync(self) -> SyncPreparation:
        manifest = self.build_manifest()
        provider = self._provider()
        upload_plan = None

        if provider == "google-drive":
            upload_plan = self.build_google_drive_plan(manifest)

        self.bus.publish(
            "sync.prepared",
            "sync",
            "Preparacao de sincronizacao concluida",
            payload={"provider": provider, "quantidade": len(manifest.items)},
        )

        return SyncPreparation(manifest=manifest, upload_plan=upload_plan)
