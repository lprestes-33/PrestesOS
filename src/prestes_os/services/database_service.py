import sqlite3
from pathlib import Path


def default_db_path() -> Path:
    return Path.home() / "PrestesOS" / "database" / "prestes.db"


class DatabaseService:
    """Responsabilidade: gerenciar a persistencia SQLite do PrestesOS."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = Path(db_path) if db_path is not None else default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.connect()
        cur = conn.cursor()

        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            origem TEXT,
            descricao TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS gravacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,
            titulo TEXT,
            pasta TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'criada'
        )
        """
        )

        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS transcricoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gravacao_id INTEGER,
            arquivo TEXT,
            texto TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
        )

        conn.commit()
        conn.close()

    def add_event(self, tipo, origem="", descricao=""):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO eventos (tipo, origem, descricao) VALUES (?, ?, ?)",
            (tipo, origem, descricao),
        )
        conn.commit()
        conn.close()

    def last_events(self, limit=10):
        conn = self.connect()
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT id, tipo, origem, descricao, criado_em FROM eventos ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return rows
