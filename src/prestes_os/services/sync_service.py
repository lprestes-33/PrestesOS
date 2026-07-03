from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import mimetypes
import os
from pathlib import Path
from urllib import error, parse, request

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
    skipped_items: list[SyncPlanItem]


@dataclass
class SyncPreparation:
    """Responsabilidade: agrupar manifesto local e plano remoto opcional."""

    manifest: SyncManifest
    upload_plan: SyncUploadPlan | None


@dataclass
class SyncUploadItemResult:
    """Responsabilidade: representar o resultado do envio de um arquivo."""

    local_path: Path
    remote_path: str
    file_id: str
    status: str


@dataclass
class SyncUploadResult:
    """Responsabilidade: representar o resultado final do upload remoto."""

    provider: str
    uploaded_at: str
    uploaded_count: int
    skipped_count: int
    items: list[SyncUploadItemResult]


@dataclass
class SyncExecution:
    """Responsabilidade: agrupar preparacao local e upload remoto opcional."""

    preparation: SyncPreparation
    upload_result: SyncUploadResult | None


@dataclass
class SyncStateEntry:
    """Responsabilidade: representar o estado persistido de um arquivo sincronizado."""

    sha256: str
    remote_path: str
    file_id: str
    synced_at: str


class SyncConfigurationError(RuntimeError):
    """Responsabilidade: sinalizar configuracao invalida para sincronizacao remota."""


class GoogleDriveClient:
    """Responsabilidade: encapsular chamadas HTTP da API do Google Drive."""

    def __init__(self, access_token: str, root_folder_id: str = "root"):
        self.access_token = access_token
        self.root_folder_id = root_folder_id

    def _request(
        self,
        method: str,
        url: str,
        *,
        query: dict | None = None,
        headers: dict | None = None,
        body: bytes | None = None,
    ) -> dict:
        target_url = url
        if query:
            target_url = f"{url}?{parse.urlencode(query)}"
        request_headers = {"Authorization": f"Bearer {self.access_token}"}
        if headers:
            request_headers.update(headers)
        http_request = request.Request(target_url, data=body, headers=request_headers, method=method)
        try:
            with request.urlopen(http_request) as response:
                payload = response.read().decode("utf-8")
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Falha na API do Google Drive: {exc.code} {details}") from exc
        return json.loads(payload) if payload else {}

    def _search_files(self, query_string: str) -> list[dict]:
        payload = self._request(
            "GET",
            "https://www.googleapis.com/drive/v3/files",
            query={
                "q": query_string,
                "fields": "files(id,name,mimeType,parents)",
                "spaces": "drive",
                "supportsAllDrives": "false",
            },
        )
        return payload.get("files", [])

    def find_folder(self, parent_id: str, folder_name: str) -> dict | None:
        safe_name = folder_name.replace("'", "\\'")
        query_string = (
            f"mimeType='application/vnd.google-apps.folder' and trashed=false "
            f"and name='{safe_name}' and '{parent_id}' in parents"
        )
        matches = self._search_files(query_string)
        return matches[0] if matches else None

    def create_folder(self, parent_id: str, folder_name: str) -> str:
        payload = self._request(
            "POST",
            "https://www.googleapis.com/drive/v3/files",
            query={"fields": "id"},
            headers={"Content-Type": "application/json; charset=utf-8"},
            body=json.dumps(
                {
                    "name": folder_name,
                    "mimeType": "application/vnd.google-apps.folder",
                    "parents": [parent_id],
                }
            ).encode("utf-8"),
        )
        return str(payload["id"])

    def ensure_folder_path(self, folder_parts: list[str]) -> str:
        current_parent = self.root_folder_id
        for folder_name in folder_parts:
            existing = self.find_folder(current_parent, folder_name)
            current_parent = str(existing["id"]) if existing else self.create_folder(current_parent, folder_name)
        return current_parent

    def find_file(self, parent_id: str, file_name: str) -> dict | None:
        safe_name = file_name.replace("'", "\\'")
        query_string = f"trashed=false and name='{safe_name}' and '{parent_id}' in parents"
        matches = self._search_files(query_string)
        return matches[0] if matches else None

    def _build_multipart_body(self, metadata: dict, content: bytes, mime_type: str) -> tuple[bytes, str]:
        boundary = "prestesos-sync-boundary"
        metadata_part = json.dumps(metadata, ensure_ascii=True).encode("utf-8")
        body = (
            f"--{boundary}\r\n"
            "Content-Type: application/json; charset=UTF-8\r\n\r\n"
        ).encode("utf-8")
        body += metadata_part
        body += (
            f"\r\n--{boundary}\r\n"
            f"Content-Type: {mime_type}\r\n\r\n"
        ).encode("utf-8")
        body += content
        body += f"\r\n--{boundary}--\r\n".encode("utf-8")
        return body, boundary

    def upload_file(self, parent_id: str, file_name: str, local_path: Path) -> tuple[str, str]:
        existing = self.find_file(parent_id, file_name)
        metadata = {"name": file_name, "parents": [parent_id]}
        content = local_path.read_bytes()
        mime_type = mimetypes.guess_type(str(local_path))[0] or "application/octet-stream"
        body, boundary = self._build_multipart_body(metadata, content, mime_type)
        headers = {"Content-Type": f"multipart/related; boundary={boundary}"}

        if existing:
            payload = self._request(
                "PATCH",
                f"https://www.googleapis.com/upload/drive/v3/files/{existing['id']}",
                query={"uploadType": "multipart", "fields": "id"},
                headers=headers,
                body=body,
            )
            return "updated", str(payload["id"])

        payload = self._request(
            "POST",
            "https://www.googleapis.com/upload/drive/v3/files",
            query={"uploadType": "multipart", "fields": "id"},
            headers=headers,
            body=body,
        )
        return "uploaded", str(payload["id"])


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

    def _sync_state_file(self) -> Path:
        return Path(self.config.get("sync.state_file")).expanduser()

    def _google_drive_config(self) -> dict:
        return self.config.get("sync.google_drive", {}) or {}

    def _google_drive_access_token(self) -> str | None:
        google_drive = self._google_drive_config()
        env_name = google_drive.get("access_token_env", "GOOGLE_DRIVE_ACCESS_TOKEN")
        if not isinstance(env_name, str) or not env_name.strip():
            return None
        return os.environ.get(env_name.strip())

    def _google_drive_root_folder_id(self) -> str:
        google_drive = self._google_drive_config()
        root_folder_id = google_drive.get("root_folder_id", "root")
        return str(root_folder_id).strip() or "root"

    def _build_google_drive_client(self) -> GoogleDriveClient:
        access_token = self._google_drive_access_token()
        if not access_token:
            raise SyncConfigurationError(
                "Configure a variavel de ambiente do token Google Drive antes de sincronizar."
            )
        return GoogleDriveClient(
            access_token=access_token,
            root_folder_id=self._google_drive_root_folder_id(),
        )

    def _hash_file(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _load_sync_state(self) -> dict[str, SyncStateEntry]:
        state_file = self._sync_state_file()
        if not state_file.exists():
            return {}

        payload = json.loads(state_file.read_text(encoding="utf-8"))
        entries = payload.get("entries", {})
        state = {}
        for relative_path, raw_entry in entries.items():
            state[relative_path] = SyncStateEntry(
                sha256=str(raw_entry.get("sha256", "")),
                remote_path=str(raw_entry.get("remote_path", "")),
                file_id=str(raw_entry.get("file_id", "")),
                synced_at=str(raw_entry.get("synced_at", "")),
            )
        return state

    def _save_sync_state(self, state: dict[str, SyncStateEntry]) -> None:
        state_file = self._sync_state_file()
        state_file.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "entries": {
                relative_path: {
                    "sha256": entry.sha256,
                    "remote_path": entry.remote_path,
                    "file_id": entry.file_id,
                    "synced_at": entry.synced_at,
                }
                for relative_path, entry in sorted(state.items())
            },
        }
        state_file.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

    def _is_item_synced(self, plan_item: SyncPlanItem, state: dict[str, SyncStateEntry]) -> bool:
        relative_key = str(plan_item.local_path.relative_to(self._base_dir()))
        current_entry = state.get(relative_key)
        if current_entry is None:
            return False
        return (
            current_entry.sha256 == plan_item.sha256
            and current_entry.remote_path == plan_item.remote_path
            and bool(current_entry.file_id)
        )

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
        state = self._load_sync_state()
        pending_items = [item for item in items if not self._is_item_synced(item, state)]
        skipped_items = [item for item in items if self._is_item_synced(item, state)]

        payload = {
            "provider": "google-drive",
            "generated_at": current_manifest.generated_at,
            "remote_root": remote_root,
            "credentials_path": str(credentials_path),
            "credentials_configured": credentials_path.exists(),
            "manifest_file": str(current_manifest.manifest_file),
            "pending_count": len(pending_items),
            "skipped_count": len(skipped_items),
            "items": [
                {
                    "category": item.category,
                    "local_path": str(item.local_path),
                    "remote_path": item.remote_path,
                    "size_bytes": item.size_bytes,
                    "sha256": item.sha256,
                }
                for item in pending_items
            ],
            "skipped_items": [
                {
                    "category": item.category,
                    "local_path": str(item.local_path),
                    "remote_path": item.remote_path,
                    "size_bytes": item.size_bytes,
                    "sha256": item.sha256,
                }
                for item in skipped_items
            ],
        }
        plan_file.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")

        self.bus.publish(
            "sync.google_drive.plan.generated",
            "sync",
            str(plan_file),
            payload={"provider": "google-drive", "quantidade": len(pending_items), "ignorados": len(skipped_items)},
        )

        return SyncUploadPlan(
            provider="google-drive",
            generated_at=current_manifest.generated_at,
            plan_file=plan_file,
            remote_root=remote_root,
            credentials_path=credentials_path,
            credentials_configured=credentials_path.exists(),
            items=pending_items,
            skipped_items=skipped_items,
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

    def upload_google_drive(self, upload_plan: SyncUploadPlan) -> SyncUploadResult:
        client = self._build_google_drive_client()
        items = []
        state = self._load_sync_state()

        self.bus.publish(
            "sync.google_drive.upload.started",
            "sync",
            "Upload para Google Drive iniciado",
            payload={"quantidade": len(upload_plan.items)},
        )

        for plan_item in upload_plan.items:
            path_parts = [part for part in Path(plan_item.remote_path).parts if part not in {".", ""}]
            folder_parts = path_parts[:-1]
            parent_id = client.ensure_folder_path(folder_parts)
            status, file_id = client.upload_file(parent_id, path_parts[-1], plan_item.local_path)
            items.append(
                SyncUploadItemResult(
                    local_path=plan_item.local_path,
                    remote_path=plan_item.remote_path,
                    file_id=file_id,
                    status=status,
                )
            )
            state[str(plan_item.local_path.relative_to(self._base_dir()))] = SyncStateEntry(
                sha256=plan_item.sha256,
                remote_path=plan_item.remote_path,
                file_id=file_id,
                synced_at=datetime.now().isoformat(timespec="seconds"),
            )
            self.bus.publish(
                "sync.google_drive.file_uploaded",
                "sync",
                str(plan_item.local_path),
                payload={"status": status, "file_id": file_id, "remote_path": plan_item.remote_path},
            )

        self._save_sync_state(state)
        result = SyncUploadResult(
            provider="google-drive",
            uploaded_at=datetime.now().isoformat(timespec="seconds"),
            uploaded_count=len(items),
            skipped_count=len(upload_plan.skipped_items),
            items=items,
        )

        self.bus.publish(
            "sync.google_drive.upload.completed",
            "sync",
            "Upload para Google Drive concluido",
            payload={"quantidade": result.uploaded_count, "ignorados": result.skipped_count},
        )
        return result

    def execute_sync(self) -> SyncExecution:
        preparation = self.prepare_sync()
        provider = self._provider()
        upload_result = None

        if provider == "google-drive" and preparation.upload_plan is not None:
            if self._google_drive_access_token():
                upload_result = self.upload_google_drive(preparation.upload_plan)
            else:
                self.bus.publish(
                    "sync.google_drive.upload.pending_auth",
                    "sync",
                    "Upload pendente por falta de token",
                    payload={"env": self._google_drive_config().get("access_token_env")},
                )

        return SyncExecution(preparation=preparation, upload_result=upload_result)
