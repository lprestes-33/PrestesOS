from pathlib import Path

import pytest

from prestes_os.services.database_service import DatabaseService
from prestes_os.services.log_service import LogService


@pytest.fixture
def prestes_base_dir(tmp_path: Path) -> Path:
    return tmp_path / "PrestesOS"


@pytest.fixture
def database_service(prestes_base_dir: Path) -> DatabaseService:
    return DatabaseService(db_path=prestes_base_dir / "database" / "prestes.db")


@pytest.fixture
def log_service(prestes_base_dir: Path) -> LogService:
    return LogService(log_file=prestes_base_dir / "logs" / "prestes.log")
