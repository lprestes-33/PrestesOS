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

        cur.execute(
            """
        CREATE TABLE IF NOT EXISTS search_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_type TEXT NOT NULL,
            source_path TEXT NOT NULL UNIQUE,
            title TEXT,
            content TEXT NOT NULL,
            metadata TEXT,
            atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
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

    def create_recording(self, tipo, titulo, pasta, status="criada"):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO gravacoes (tipo, titulo, pasta, status) VALUES (?, ?, ?, ?)",
            (tipo, titulo, str(pasta), status),
        )
        recording_id = cur.lastrowid
        conn.commit()
        conn.close()
        return recording_id

    def update_recording_status(self, recording_id, status):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "UPDATE gravacoes SET status = ? WHERE id = ?",
            (status, recording_id),
        )
        conn.commit()
        conn.close()

    def get_recording(self, recording_id):
        conn = self.connect()
        cur = conn.cursor()
        row = cur.execute(
            "SELECT id, tipo, titulo, pasta, criado_em, status FROM gravacoes WHERE id = ?",
            (recording_id,),
        ).fetchone()
        conn.close()
        return row

    def create_transcription(self, gravacao_id, arquivo, texto):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO transcricoes (gravacao_id, arquivo, texto) VALUES (?, ?, ?)",
            (gravacao_id, str(arquivo), texto),
        )
        transcription_id = cur.lastrowid
        conn.commit()
        conn.close()
        return transcription_id

    def list_transcriptions(self, gravacao_id):
        conn = self.connect()
        cur = conn.cursor()
        rows = cur.execute(
            "SELECT id, gravacao_id, arquivo, texto, criado_em FROM transcricoes WHERE gravacao_id = ? ORDER BY id ASC",
            (gravacao_id,),
        ).fetchall()
        conn.close()
        return rows

    def upsert_search_document(self, source_type, source_path, title, content, metadata=""):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO search_index (source_type, source_path, title, content, metadata, atualizado_em)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(source_path) DO UPDATE SET
                source_type=excluded.source_type,
                title=excluded.title,
                content=excluded.content,
                metadata=excluded.metadata,
                atualizado_em=CURRENT_TIMESTAMP
            """,
            (source_type, str(source_path), title, content, metadata),
        )
        conn.commit()
        conn.close()

    def search_documents(self, query, limit=10):
        conn = self.connect()
        cur = conn.cursor()
        if query == "":
            rows = cur.execute(
                """
                SELECT id, source_type, source_path, title, content, metadata, atualizado_em
                FROM search_index
                ORDER BY atualizado_em DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            conn.close()
            return rows
        pattern = f"%{query}%"
        rows = cur.execute(
            """
            SELECT id, source_type, source_path, title, content, metadata, atualizado_em
            FROM search_index
            WHERE content LIKE ? OR title LIKE ?
            ORDER BY atualizado_em DESC, id DESC
            LIMIT ?
            """,
            (pattern, pattern, limit),
        ).fetchall()
        conn.close()
        return rows
