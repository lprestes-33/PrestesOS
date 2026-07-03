from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import subprocess

from prestes_os.services.config_service import ConfigService
from prestes_os.services.database_service import DatabaseService
from prestes_os.services.event_bus import EventBus


SUPPORTED_AUDIO_EXTENSIONS = {".opus", ".m4a", ".mp3", ".wav"}


@dataclass
class TranscriptionPreparation:
    """Responsabilidade: representar os artefatos preparados para transcricao."""

    source_folder: Path
    output_folder: Path
    converted_files: list[Path]


@dataclass
class TranscriptionArtifact:
    """Responsabilidade: representar os arquivos gerados para um WAV transcrito."""

    wav_file: Path
    txt_file: Path
    srt_file: Path
    json_file: Path
    text: str


@dataclass
class TranscriptionResult:
    """Responsabilidade: representar o resultado consolidado da transcricao."""

    source_folder: Path
    output_folder: Path
    artifacts: list[TranscriptionArtifact]
    consolidated_file: Path
    recording_id: int | None


class TranscriptionService:
    """Responsabilidade: preparar e executar o pipeline de transcricao."""

    def __init__(
        self,
        config_service: ConfigService | None = None,
        event_bus: EventBus | None = None,
        database_service: DatabaseService | None = None,
        ffmpeg_runner=None,
        whisper_runner=None,
    ):
        self.config = config_service or ConfigService()
        self.db = database_service or DatabaseService()
        self.bus = event_bus or EventBus(db_service=self.db)
        self.ffmpeg_runner = ffmpeg_runner or subprocess.run
        self.whisper_runner = whisper_runner or subprocess.run

    def _recording_sort_key(self, folder: Path):
        try:
            day_value = datetime.strptime(folder.parent.name, "%d%m%Y")
        except ValueError:
            day_value = datetime.min
        return (day_value, folder.stat().st_mtime, folder.name)

    def _run_command(self, runner, args, missing_dependency_message):
        try:
            runner(
                args,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(missing_dependency_message) from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Falha ao executar comando: {' '.join(args)}") from exc

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

        self._run_command(self.ffmpeg_runner, command, "ffmpeg nao esta disponivel neste ambiente.")

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

    def read_recording_id(self, recording_folder: Path) -> int | None:
        metadata_file = recording_folder / "metadata.txt"
        if not metadata_file.exists():
            return None

        for line in metadata_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("recording_id="):
                _, value = line.split("=", 1)
                return int(value.strip())
        return None

    def transcribe_wav_file(self, wav_file: Path, output_folder: Path) -> TranscriptionArtifact:
        model_path = Path(self.config.get("audio.modelo_whisper")).expanduser()
        if not model_path.exists():
            raise RuntimeError(f"Modelo whisper nao encontrado: {model_path}")

        whisper_command = self.config.get("audio.comando_whisper", "whisper-cli")
        language = self.config.get("audio.idioma", "pt")
        output_base = output_folder / wav_file.stem

        command = [
            whisper_command,
            "-m",
            str(model_path),
            "-f",
            str(wav_file),
            "-l",
            str(language),
            "-otxt",
            "-osrt",
            "-oj",
            "-of",
            str(output_base),
        ]

        self.bus.publish(
            "transcription.file.started",
            "transcription",
            str(wav_file),
            payload={"arquivo_wav": str(wav_file)},
        )

        self._run_command(
            self.whisper_runner,
            command,
            "Whisper.cpp nao esta disponivel neste ambiente.",
        )

        txt_file = output_base.with_suffix(".txt")
        srt_file = output_base.with_suffix(".srt")
        json_file = output_base.with_suffix(".json")
        for output_file in (txt_file, srt_file, json_file):
            if not output_file.exists():
                raise RuntimeError(f"Arquivo de transcricao esperado nao foi gerado: {output_file.name}")

        text = txt_file.read_text(encoding="utf-8").strip()
        self.bus.publish(
            "transcription.file.completed",
            "transcription",
            str(txt_file),
            payload={"arquivo_wav": str(wav_file), "arquivo_txt": str(txt_file)},
        )
        return TranscriptionArtifact(
            wav_file=wav_file,
            txt_file=txt_file,
            srt_file=srt_file,
            json_file=json_file,
            text=text,
        )

    def write_consolidated_transcription(self, artifacts: list[TranscriptionArtifact], output_folder: Path) -> Path:
        consolidated_file = output_folder / "TRANSCRICAO_COMPLETA.txt"
        content = "\n\n".join(artifact.text for artifact in artifacts if artifact.text.strip())
        consolidated_file.write_text(content + ("\n" if content else ""), encoding="utf-8")
        return consolidated_file

    def persist_transcriptions(self, recording_id: int | None, artifacts: list[TranscriptionArtifact]):
        if recording_id is None:
            return
        for artifact in artifacts:
            self.db.create_transcription(recording_id, artifact.txt_file, artifact.text)

    def transcribe_latest_recording(self) -> TranscriptionResult:
        preparation = self.prepare_latest_recording()
        recording_id = self.read_recording_id(preparation.source_folder)

        self.bus.publish(
            "transcription.started",
            "transcription",
            str(preparation.source_folder),
            payload={"recording_id": recording_id, "pasta_saida": str(preparation.output_folder)},
        )

        try:
            artifacts = [
                self.transcribe_wav_file(wav_file, preparation.output_folder)
                for wav_file in preparation.converted_files
            ]
            consolidated_file = self.write_consolidated_transcription(artifacts, preparation.output_folder)
            self.persist_transcriptions(recording_id, artifacts)
            self.bus.publish(
                "transcription.completed",
                "transcription",
                str(consolidated_file),
                payload={
                    "recording_id": recording_id,
                    "arquivo_consolidado": str(consolidated_file),
                },
            )
            return TranscriptionResult(
                source_folder=preparation.source_folder,
                output_folder=preparation.output_folder,
                artifacts=artifacts,
                consolidated_file=consolidated_file,
                recording_id=recording_id,
            )
        except Exception as exc:
            self.bus.publish(
                "transcription.failed",
                "transcription",
                str(exc),
                payload={"recording_id": recording_id},
            )
            raise
