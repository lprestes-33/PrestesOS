from dataclasses import dataclass
from pathlib import Path

from prestes_os.services.config_service import ConfigService
from prestes_os.services.database_service import DatabaseService
from prestes_os.services.event_bus import EventBus


@dataclass
class SearchResult:
    """Responsabilidade: representar um resultado de busca textual."""

    source_type: str
    source_path: Path
    title: str
    snippet: str


class SearchService:
    """Responsabilidade: indexar e consultar conhecimento textual local do PrestesOS."""

    def __init__(
        self,
        config_service: ConfigService | None = None,
        database_service: DatabaseService | None = None,
        event_bus: EventBus | None = None,
    ):
        self.config = config_service or ConfigService()
        self.db = database_service or DatabaseService()
        self.bus = event_bus or EventBus(db_service=self.db)

    def _transcriptions_dir(self) -> Path:
        return Path(self.config.get("audio.transcricoes_dir")).expanduser()

    def _summaries_dir(self) -> Path:
        return Path(self.config.get("ai.resumos_dir")).expanduser()

    def _collect_documents(self) -> list[tuple[str, Path]]:
        documents = []
        transcriptions_dir = self._transcriptions_dir()
        summaries_dir = self._summaries_dir()

        if transcriptions_dir.exists():
            documents.extend(("transcription", path) for path in transcriptions_dir.glob("*/*/TRANSCRICAO_COMPLETA.txt"))
        if summaries_dir.exists():
            documents.extend(("summary", path) for path in summaries_dir.glob("*/*/RESUMO_*.txt"))

        return sorted(documents, key=lambda item: str(item[1]))

    def _build_title(self, source_type: str, path: Path) -> str:
        prefix = "Transcricao" if source_type == "transcription" else "Resumo"
        return f"{prefix}: {path.parent.name}"

    def reindex_documents(self) -> int:
        indexed = 0
        for source_type, path in self._collect_documents():
            content = path.read_text(encoding="utf-8").strip()
            title = self._build_title(source_type, path)
            metadata = f"folder={path.parent.name}"
            self.db.upsert_search_document(source_type, path, title, content, metadata)
            indexed += 1

        self.bus.publish(
            "search.reindex.completed",
            "search",
            f"{indexed} documentos indexados",
            payload={"quantidade": indexed},
        )
        return indexed

    def _build_snippet(self, content: str, query: str, max_length: int = 140) -> str:
        lower_content = content.lower()
        lower_query = query.lower()
        position = lower_content.find(lower_query)
        if position == -1:
            snippet = content[:max_length]
        else:
            start = max(position - 40, 0)
            end = min(position + len(query) + 80, len(content))
            snippet = content[start:end]
        return snippet.replace("\n", " ").strip()

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        if not query.strip():
            raise ValueError("A busca precisa de um termo nao vazio.")

        rows = self.db.search_documents(query.strip(), limit=limit)
        results = [
            SearchResult(
                source_type=row[1],
                source_path=Path(row[2]),
                title=row[3] or row[2],
                snippet=self._build_snippet(row[4], query),
            )
            for row in rows
        ]

        self.bus.publish(
            "search.query.completed",
            "search",
            query,
            payload={"quantidade": len(results), "consulta": query},
        )
        return results
