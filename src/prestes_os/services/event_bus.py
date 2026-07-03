from prestes_os.services.database_service import DatabaseService
from prestes_os.services.log_service import LogService


class EventBus:
    """Responsabilidade: desacoplar a comunicacao por eventos entre modulos."""

    def __init__(
        self,
        db_service: DatabaseService | None = None,
        log_service: LogService | None = None,
    ):
        self.db = db_service or DatabaseService()
        self.log = log_service or LogService()
        self.listeners = {}

    def subscribe(self, event_type, callback):
        self.listeners.setdefault(event_type, []).append(callback)

    def publish(self, event_type, origem="", descricao="", payload=None):
        self.db.add_event(event_type, origem, descricao)
        self.log.info(f"EVENT {event_type} | {origem} | {descricao}")

        for callback in self.listeners.get(event_type, []):
            callback(payload or {})
