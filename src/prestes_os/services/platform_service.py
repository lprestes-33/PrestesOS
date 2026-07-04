from dataclasses import dataclass
from pathlib import Path

from prestes_os.services.calendar_service import CalendarService
from prestes_os.services.config_service import ConfigService
from prestes_os.services.database_service import DatabaseService
from prestes_os.services.event_bus import EventBus
from prestes_os.services.gmail_service import GmailService
from prestes_os.services.log_service import LogService
from prestes_os.services.notebooklm_service import NotebookLMService
from prestes_os.services.sync_service import SyncService


@dataclass
class PlatformCheck:
    """Responsabilidade: representar uma verificacao consolidada da plataforma."""

    key: str
    title: str
    status: str
    message: str
    details: dict


@dataclass
class PlatformStatus:
    """Responsabilidade: agrupar o diagnostico local para fechamento operacional da v1.0."""

    target_version: str
    core_ready: bool
    checks: list[PlatformCheck]


class PlatformService:
    """Responsabilidade: consolidar o status local da plataforma em um unico diagnostico."""

    def __init__(
        self,
        config_service: ConfigService | None = None,
        database_service: DatabaseService | None = None,
        event_bus: EventBus | None = None,
        log_service: LogService | None = None,
    ):
        self.config = config_service or ConfigService()
        self.database = database_service or DatabaseService()
        self.log_service = log_service or LogService()
        self.bus = event_bus or EventBus(db_service=self.database, log_service=self.log_service)
        self.sync_service = SyncService(config_service=self.config, event_bus=self.bus)
        self.gmail_service = GmailService(config_service=self.config, event_bus=self.bus)
        self.calendar_service = CalendarService(config_service=self.config, event_bus=self.bus)
        self.notebooklm_service = NotebookLMService(config_service=self.config, event_bus=self.bus)

    def _config_file(self) -> Path:
        return Path(self.config.config_path).expanduser()

    def _logs_file(self) -> Path:
        return Path(self.config.get("logs.path")).expanduser()

    def _build_core_checks(self) -> list[PlatformCheck]:
        config_file = self._config_file()
        logs_file = self._logs_file()
        base_dir = Path(self.config.get("base_dir")).expanduser()
        sync_runs = self.sync_service.read_sync_runs()
        sync_failures = self.sync_service.read_sync_failures()

        return [
            PlatformCheck(
                key="config",
                title="Configuracao",
                status="ok" if config_file.exists() else "warning",
                message="Configuracao principal encontrada." if config_file.exists() else "Configuracao principal ausente.",
                details={
                    "base_dir": str(base_dir),
                    "config_file": str(config_file),
                },
            ),
            PlatformCheck(
                key="database",
                title="Banco SQLite",
                status="ok" if self.database.db_path.exists() else "warning",
                message="Banco local pronto para uso." if self.database.db_path.exists() else "Banco local ainda nao foi criado.",
                details={
                    "db_path": str(self.database.db_path),
                    "recordings": self.database.count_recordings(),
                    "transcriptions": self.database.count_transcriptions(),
                    "search_documents": self.database.count_search_documents(),
                },
            ),
            PlatformCheck(
                key="logs",
                title="Logs Estruturados",
                status="ok" if logs_file.exists() else "warning",
                message="Log estruturado disponivel." if logs_file.exists() else "Log estruturado ainda nao foi gerado.",
                details={
                    "log_file": str(logs_file),
                },
            ),
            PlatformCheck(
                key="sync",
                title="Sincronizacao",
                status="ok",
                message="Sync basico preparado com manifesto, historico e resumo por execucao.",
                details={
                    "provider": self.config.get("sync.provider", "local-manifest"),
                    "runs": sync_runs.total_items,
                    "recent_failures": sync_failures.total_items,
                    "manifest_dir": str(self.config.get("sync.manifest_dir")),
                },
            ),
        ]

    def _build_optional_checks(self) -> list[PlatformCheck]:
        google_drive_auth = self.sync_service.resolve_google_drive_auth()
        gmail_status = self.gmail_service.status()
        calendar_status = self.calendar_service.status()
        notebooklm_status = self.notebooklm_service.status()

        return [
            PlatformCheck(
                key="google_drive",
                title="Google Drive",
                status="ok" if google_drive_auth.access_token else "warning",
                message=google_drive_auth.message,
                details={
                    "source": google_drive_auth.source,
                    "credentials_path": str(google_drive_auth.credentials_path),
                    "expired": google_drive_auth.is_expired,
                },
            ),
            PlatformCheck(
                key="gmail",
                title="Gmail",
                status="ok" if gmail_status.auth.access_token else "warning",
                message=gmail_status.auth.message,
                details={
                    "source": gmail_status.auth.source,
                    "default_query": gmail_status.default_query,
                    "max_results": gmail_status.max_results,
                },
            ),
            PlatformCheck(
                key="calendar",
                title="Google Calendar",
                status="ok" if calendar_status.auth.access_token else "warning",
                message=calendar_status.auth.message,
                details={
                    "source": calendar_status.auth.source,
                    "default_calendar_id": calendar_status.default_calendar_id,
                    "days_ahead": calendar_status.days_ahead,
                },
            ),
            PlatformCheck(
                key="notebooklm",
                title="NotebookLM",
                status="ok" if notebooklm_status.auth.access_token else "warning",
                message=notebooklm_status.auth.message,
                details={
                    "source": notebooklm_status.auth.source,
                    "default_notebook": notebooklm_status.default_notebook,
                    "max_sources": notebooklm_status.max_sources,
                },
            ),
        ]

    def status(self) -> PlatformStatus:
        checks = self._build_core_checks() + self._build_optional_checks()
        core_ready = all(check.status == "ok" for check in checks if check.key in {"config", "database", "logs", "sync"})
        report = PlatformStatus(target_version="v1.0", core_ready=core_ready, checks=checks)
        self.bus.publish(
            "platform.status.checked",
            "platform",
            "Diagnostico local consolidado",
            payload={
                "target_version": report.target_version,
                "core_ready": report.core_ready,
                "checks": len(report.checks),
            },
        )
        return report
