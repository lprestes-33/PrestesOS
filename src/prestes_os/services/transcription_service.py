from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import subprocess

from prestes_os.services.config_service import ConfigService
from prestes_os.services.event_bus import EventBus


SUPPORTED_AUDIO_EXTENSIONS = {".opus", ".m4a", ".mp3", ".wav"}


@dataclass
class TranscriptionPreparation:
    """Responsabilidade: representar os artefatos preparados para transcricao."""

    source_folder: Path
    output_folder: Path
    converted_files: list[Path]


class TranscriptionService:
    """Responsabilidade: preparar gravacoes para o pipeline de transcricao."""

    def __init__(
        self,
        config_service: ConfigService | None = None,
        event_bus: EventBus | None = None,
        command_runner=None,
    ):
        self.config = config_service or ConfigService()
        self.bus = event_bus or EventBus()
        self.command_runner = command_runner or subprocess.run

    def _recording_sort_key(self, folder: Path):
        try:
            day_value = datetime.strptime(folder.parent.name, "%d%m%Y")
        except ValueError:
            day_value = datetime.min
        return (day_value, folder.stat().st_mtime, folder.name)

    def find_latest_recording_folder(self) -> Path:
        recordings_dir = Path(self.config.get("audio.gravacoes_dir")).expanduser()
        if not recordings_dir.exists():
            raise FileNotFoundError("Diretorio de gravacoes nao encontrado.")

        candidates = [path for path in recordings_dir.glob("*/*") if path.is_dir()]
        if not candidates:
            raise FileNotFoundError("Nenhuma gravacao encontrada para transcricao.")

        return max(candidates, key=self._recording_sort_key)

    def list_supported_audio_files(self, recording_folder: Path) -> list[Path]:
        files = [
            path
            for path in sorted(recording_folder.iterdir())
            if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
        ]
        if not files:
            raise FileNotFoundError("Nenhum arquivo de audio suportado encontrado na gravacao.")
        return files

    def build_output_folder(self, recording_folder: Path) -> Path:
        transcriptions_dir = Path(self.config.get("audio.transcricoes_dir")).expanduser()
        output_folder = transcriptions_dir / recording_folder.parent.name / recording_folder.name
        output_folder.mkdir(parents=True, exist_ok=True)
        return output_folder

    def convert_to_wav(self, source_file: Path, output_folder: Path) -> Path:
        output_file = output_folder / f"{source_file.stem}.wav"
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(source_file),
            "-ar",
            "16000",
            "-ac",
            "1",
            str(output_file),
        ]

        try:
            self.command_runner(
                command,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("ffmpeg nao esta disponivel neste ambiente.") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Falha ao converter arquivo para WAV: {source_file.name}") from exc

        self.bus.publish(
            "transcription.file.converted",
            "transcription",
            str(output_file),
            payload={"arquivo_origem": str(source_file), "arquivo_wav": str(output_file)},
        )
        return output_file

    def prepare_latest_recording(self) -> TranscriptionPreparation:
        source_folder = self.find_latest_recording_folder()
        audio_files = self.list_supported_audio_files(source_folder)
        output_folder = self.build_output_folder(source_folder)

        self.bus.publish(
            "transcription.preparation.started",
            "transcription",
            str(source_folder),
            payload={"pasta_origem": str(source_folder), "pasta_saida": str(output_folder)},
        )

        converted_files = [self.convert_to_wav(audio_file, output_folder) for audio_file in audio_files]

        self.bus.publish(
            "transcription.preparation.completed",
            "transcription",
            str(output_folder),
            payload={
                "pasta_origem": str(source_folder),
                "pasta_saida": str(output_folder),
                "arquivos_convertidos": [str(path) for path in converted_files],
            },
        )

        return TranscriptionPreparation(
            source_folder=source_folder,
            output_folder=output_folder,
            converted_files=converted_files,
        )
