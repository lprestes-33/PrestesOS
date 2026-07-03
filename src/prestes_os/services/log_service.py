from datetime import datetime
from pathlib import Path


def default_log_file() -> Path:
    return Path.home() / "PrestesOS" / "logs" / "prestes.log"


class LogService:
    """Responsabilidade: registrar eventos operacionais relevantes do sistema."""

    def __init__(self, log_file: Path | None = None):
        self.log_file = Path(log_file) if log_file is not None else default_log_file()
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def write(self, level, message):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{now}] [{level.upper()}] {message}\n"
        with self.log_file.open("a", encoding="utf-8") as file_handle:
            file_handle.write(line)

    def info(self, message):
        self.write("info", message)

    def warning(self, message):
        self.write("warning", message)

    def error(self, message):
        self.write("error", message)
