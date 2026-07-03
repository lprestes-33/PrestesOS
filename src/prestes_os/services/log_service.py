from datetime import datetime
import json
from pathlib import Path


def default_log_file() -> Path:
    return Path.home() / "PrestesOS" / "logs" / "prestes.log"


class LogService:
    """Responsabilidade: registrar eventos operacionais relevantes do sistema."""

    def __init__(self, log_file: Path | None = None):
        self.log_file = Path(log_file) if log_file is not None else default_log_file()
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def write(self, level, message, source="system", event_type=None, context=None):
        payload = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "level": level.upper(),
            "message": message,
            "source": source,
            "event_type": event_type,
            "context": context or {},
        }
        with self.log_file.open("a", encoding="utf-8") as file_handle:
            file_handle.write(json.dumps(payload, ensure_ascii=True) + "\n")

    def info(self, message, source="system", event_type=None, context=None):
        self.write("info", message, source=source, event_type=event_type, context=context)

    def warning(self, message, source="system", event_type=None, context=None):
        self.write("warning", message, source=source, event_type=event_type, context=context)

    def error(self, message, source="system", event_type=None, context=None):
        self.write("error", message, source=source, event_type=event_type, context=context)
