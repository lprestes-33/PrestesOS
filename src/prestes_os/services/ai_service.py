from dataclasses import dataclass
import os
from pathlib import Path

from prestes_os.services.config_service import ConfigService
from prestes_os.services.event_bus import EventBus


@dataclass
class AIResult:
    """Responsabilidade: representar o resumo gerado pelo AIService."""

    source_file: Path
    output_file: Path
    summary_type: str
    content: str
    mode: str


@dataclass
class AISettings:
    """Responsabilidade: representar a configuracao efetiva do AIService."""

    mode: str
    provider: str
    openai_model: str
    has_openai_key: bool


class AIService:
    """Responsabilidade: gerar resumos a partir das transcricoes do PrestesOS."""

    def __init__(
        self,
        config_service: ConfigService | None = None,
        event_bus: EventBus | None = None,
        environment: dict | None = None,
    ):
        self.config = config_service or ConfigService()
        self.bus = event_bus or EventBus()
        self.environment = environment if environment is not None else os.environ

    def _transcriptions_dir(self) -> Path:
        return Path(self.config.get("audio.transcricoes_dir")).expanduser()

    def _summaries_dir(self) -> Path:
        return Path(self.config.get("ai.resumos_dir")).expanduser()

    def _recordings_dir(self) -> Path:
        return Path(self.config.get("audio.gravacoes_dir")).expanduser()

    def load_settings(self) -> AISettings:
        mode = self.config.get("ai.mode", "offline")
        provider = self.config.get("ai.provider", "local-placeholder")
        model = self.environment.get("OPENAI_MODEL") or self.config.get("ai.openai_model", "gpt-4.1-mini")
        api_key = self.environment.get("OPENAI_API_KEY", "").strip()
        has_openai_key = bool(api_key)

        if mode == "openai" and not has_openai_key:
            mode = "offline"

        return AISettings(
            mode=mode,
            provider=provider,
            openai_model=model,
            has_openai_key=has_openai_key,
        )

    def find_latest_transcription_file(self) -> Path:
        transcriptions_dir = self._transcriptions_dir()
        if not transcriptions_dir.exists():
            raise FileNotFoundError("Diretorio de transcricoes nao encontrado.")

        candidates = list(transcriptions_dir.glob("*/*/TRANSCRICAO_COMPLETA.txt"))
        if not candidates:
            raise FileNotFoundError("Nenhuma transcricao consolidada encontrada.")

        return max(candidates, key=lambda path: path.stat().st_mtime)

    def detect_summary_type(self, transcription_file: Path, explicit_type: str | None = None) -> str:
        if explicit_type:
            return explicit_type

        day_folder = transcription_file.parent.parent.name
        recording_folder = transcription_file.parent.name
        metadata_file = self._recordings_dir() / day_folder / recording_folder / "metadata.txt"
        if metadata_file.exists():
            for line in metadata_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("tipo="):
                    _, value = line.split("=", 1)
                    return value.strip() or "Outro"
        return "Outro"

    def build_output_file(self, transcription_file: Path, summary_type: str) -> Path:
        output_dir = self._summaries_dir() / transcription_file.parent.parent.name / transcription_file.parent.name
        output_dir.mkdir(parents=True, exist_ok=True)
        safe_type = summary_type.upper().replace(" ", "_")
        return output_dir / f"RESUMO_{safe_type}.txt"

    def _extract_sentences(self, text: str, limit: int = 3) -> list[str]:
        normalized = text.replace("\r", " ").replace("\n", " ")
        chunks = [part.strip() for part in normalized.split(".") if part.strip()]
        return chunks[:limit]

    def _build_offline_summary(self, text: str, summary_type: str) -> str:
        word_count = len(text.split())
        highlights = self._extract_sentences(text, limit=3)
        header_map = {
            "Aula": "Resumo de Aula",
            "Reuniao": "Ata de Reuniao",
            "Conversa": "Resumo de Conversa",
            "Outro": "Resumo Geral",
        }
        header = header_map.get(summary_type, "Resumo Geral")

        lines = [
            header,
            "",
            "Modo: offline-placeholder",
            f"Tipo identificado: {summary_type}",
            f"Palavras analisadas: {word_count}",
            "",
            "Pontos principais:",
        ]

        if highlights:
            for item in highlights:
                lines.append(f"- {item}.")
        else:
            lines.append("- Transcricao sem conteudo suficiente para destacar pontos principais.")

        if summary_type == "Aula":
            lines.extend(
                [
                    "",
                    "Sugestao de estudo:",
                    "- Revisar os conceitos centrais destacados acima.",
                ]
            )
        elif summary_type == "Reuniao":
            lines.extend(
                [
                    "",
                    "Encaminhamento sugerido:",
                    "- Confirmar responsaveis e prazos a partir dos pontos principais.",
                ]
            )
        elif summary_type == "Conversa":
            lines.extend(
                [
                    "",
                    "Leitura sugerida:",
                    "- Registrar temas recorrentes e decisoes implicitas.",
                ]
            )

        return "\n".join(lines) + "\n"

    def _build_openai_ready_message(self, summary_type: str, settings: AISettings) -> str:
        return (
            f"Resumo {summary_type}\n\n"
            f"Modo: openai-preparado\n"
            f"Provider: {settings.provider}\n"
            f"Modelo configurado: {settings.openai_model}\n"
            "Integracao de rede ainda nao ativada nesta etapa.\n"
        )

    def summarize_latest_transcription(self, summary_type: str | None = None) -> AIResult:
        source_file = self.find_latest_transcription_file()
        detected_type = self.detect_summary_type(source_file, explicit_type=summary_type)
        output_file = self.build_output_file(source_file, detected_type)
        text = source_file.read_text(encoding="utf-8").strip()
        settings = self.load_settings()

        self.bus.publish(
            "ai.summary.started",
            "ai",
            str(source_file),
            payload={"tipo": detected_type, "modo": settings.mode, "provider": settings.provider},
        )

        if self.config.get("ai.mode", "offline") == "openai" and not settings.has_openai_key:
            raise RuntimeError("OPENAI_API_KEY ausente. Defina a variavel de ambiente ou use ai.mode=offline.")

        if settings.mode == "offline":
            content = self._build_offline_summary(text, detected_type)
        elif settings.mode == "openai":
            content = self._build_openai_ready_message(detected_type, settings)
        else:
            raise RuntimeError(f"Modo de IA nao suportado: {settings.mode}")

        output_file.write_text(content, encoding="utf-8")

        self.bus.publish(
            "ai.summary.completed",
            "ai",
            str(output_file),
            payload={
                "tipo": detected_type,
                "modo": settings.mode,
                "provider": settings.provider,
                "arquivo_saida": str(output_file),
            },
        )

        return AIResult(
            source_file=source_file,
            output_file=output_file,
            summary_type=detected_type,
            content=content,
            mode=settings.mode,
        )
