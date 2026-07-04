from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path

from prestes_os.services.config_service import ConfigService
from prestes_os.services.event_bus import EventBus


@dataclass
class GmailAuthState:
    """Responsabilidade: representar o estado efetivo da autenticacao Gmail."""

    source: str
    access_token: str | None
    credentials_path: Path
    expires_at: str | None
    is_expired: bool
    message: str


@dataclass
class GmailStatus:
    """Responsabilidade: representar o status local da integracao Gmail."""

    provider: str
    auth: GmailAuthState
    default_query: str
    max_results: int


class GmailService:
    """Responsabilidade: preparar a integracao futura do PrestesOS com Gmail."""

    def __init__(
        self,
        config_service: ConfigService | None = None,
        event_bus: EventBus | None = None,
        environment: dict | None = None,
    ):
        self.config = config_service or ConfigService()
        self.bus = event_bus or EventBus()
        self.environment = environment if environment is not None else os.environ

    def _gmail_config(self) -> dict:
        return self.config.get("gmail", {}) or {}

    def _credentials_path(self) -> Path:
        return Path(self.config.get("gmail.credentials_path")).expanduser()

    def _credentials_payload(self) -> dict:
        credentials_path = self._credentials_path()
        if not credentials_path.exists():
            return {}
        return json.loads(credentials_path.read_text(encoding="utf-8"))

    def _token_env_name(self) -> str:
        env_name = self.config.get("gmail.access_token_env", "GMAIL_ACCESS_TOKEN")
        return str(env_name).strip() or "GMAIL_ACCESS_TOKEN"

    def _credentials_access_token_key(self) -> str:
        key_name = self.config.get("gmail.credentials_access_token_key", "access_token")
        return str(key_name).strip() or "access_token"

    def _credentials_expires_at_key(self) -> str:
        key_name = self.config.get("gmail.credentials_expires_at_key", "expires_at")
        return str(key_name).strip() or "expires_at"

    def _is_expired(self, expires_at: str | None) -> bool:
        if not expires_at:
            return False
        normalized = expires_at.replace("Z", "+00:00")
        try:
            expires_at_dt = datetime.fromisoformat(normalized)
        except ValueError:
            return False
        return expires_at_dt <= datetime.now(expires_at_dt.tzinfo)

    def resolve_auth(self) -> GmailAuthState:
        env_name = self._token_env_name()
        env_token = self.environment.get(env_name)
        credentials_path = self._credentials_path()

        if env_token:
            return GmailAuthState(
                source="env",
                access_token=env_token,
                credentials_path=credentials_path,
                expires_at=None,
                is_expired=False,
                message=f"Token Gmail carregado da variavel de ambiente {env_name}.",
            )

        payload = self._credentials_payload()
        access_token = payload.get(self._credentials_access_token_key())
        expires_at = payload.get(self._credentials_expires_at_key())
        is_expired = self._is_expired(str(expires_at) if expires_at is not None else None)

        if isinstance(access_token, str) and access_token.strip() and not is_expired:
            return GmailAuthState(
                source="file",
                access_token=access_token.strip(),
                credentials_path=credentials_path,
                expires_at=str(expires_at) if expires_at is not None else None,
                is_expired=False,
                message=f"Token Gmail carregado do arquivo {credentials_path}.",
            )

        if isinstance(access_token, str) and access_token.strip() and is_expired:
            return GmailAuthState(
                source="file-expired",
                access_token=None,
                credentials_path=credentials_path,
                expires_at=str(expires_at),
                is_expired=True,
                message=f"Token Gmail do arquivo {credentials_path} esta expirado.",
            )

        return GmailAuthState(
            source="missing",
            access_token=None,
            credentials_path=credentials_path,
            expires_at=None,
            is_expired=False,
            message="Nenhum token Gmail valido foi encontrado.",
        )

    def status(self) -> GmailStatus:
        auth = self.resolve_auth()
        status = GmailStatus(
            provider=self.config.get("gmail.provider", "gmail-api-preparado"),
            auth=auth,
            default_query=self.config.get("gmail.default_query", "label:inbox newer_than:7d"),
            max_results=self.config.get("gmail.max_results", 20),
        )
        self.bus.publish(
            "gmail.status.checked",
            "gmail",
            status.provider,
            payload={
                "source": auth.source,
                "autenticado": bool(auth.access_token),
                "query": status.default_query,
                "max_results": status.max_results,
            },
        )
        return status
