from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import signal
import subprocess
import time
import unicodedata

from prestes_os.services.config_service import ConfigService
from prestes_os.services.database_service import DatabaseService
from prestes_os.services.event_bus import EventBus


@dataclass
class RecordingSession:
    """Responsabilidade: representar o contexto de uma sessao de gravacao."""

    recording_id: int
    tipo: str
    titulo: str
    folder: Path
    started_at: datetime
    part_duration_seconds: int


class AudioService:
    """Responsabilidade: coordenar o ciclo de gravacao de audio no PrestesOS."""

    def __init__(
        self,
        config_service: ConfigService | None = None,
        event_bus: EventBus | None = None,
        database_service: DatabaseService | None = None,
        command_runner=None,
        sleep_fn=None,
        signal_module=signal,
        clock=None,
    ):
        self.config = config_service or ConfigService()
        self.db = database_service or DatabaseService()
        self.bus = event_bus or EventBus(db_service=self.db)
        self.command_runner = command_runner or subprocess.run
        self.sleep_fn = sleep_fn or time.sleep
        self.signal_module = signal_module
        self.clock = clock or datetime.now
        self.running = True
        self.active_session: RecordingSession | None = None

    def slug(self, text):
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"[^a-zA-Z0-9_-]+", "_", text).strip("_")
        return text or "gravacao"

    def stop(self, *_):
        self.running = False
        self._stop_termux_recording()
        if self.active_session is not None:
            self.db.update_recording_status(self.active_session.recording_id, "interrompida")
            self.bus.publish(
                "recording.stopped",
                "audio",
                f"Gravacao interrompida: {self.active_session.folder}",
                payload={"recording_id": self.active_session.recording_id},
            )

    def _run_command(self, args, check=True):
        try:
            return self.command_runner(
                args,
                check=check,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("termux-microphone-record nao esta disponivel neste ambiente.") from exc
        except subprocess.CalledProcessError as exc:
            joined = " ".join(args)
            raise RuntimeError(f"Falha ao executar comando de audio: {joined}") from exc

    def _stop_termux_recording(self):
        self._run_command(["termux-microphone-record", "-q"], check=False)

    def _build_session(self, tipo="Outro", titulo=None):
        duration_minutes = int(self.config.get("audio.duracao_parte_minutos", 30))
        recordings_dir = Path(self.config.get("audio.gravacoes_dir")).expanduser()

        now = self.clock()
        day = now.strftime("%d%m%Y")
        hour = now.strftime("%Hh%Mm%Ss")
        final_title = titulo or f"{tipo}_{day}_{hour}"

        folder = recordings_dir / day / self.slug(final_title)
        folder.mkdir(parents=True, exist_ok=True)

        recording_id = self.db.create_recording(
            tipo=tipo,
            titulo=final_title,
            pasta=folder,
            status="gravando",
        )

        session = RecordingSession(
            recording_id=recording_id,
            tipo=tipo,
            titulo=final_title,
            folder=folder,
            started_at=now,
            part_duration_seconds=duration_minutes * 60,
        )
        self.active_session = session
        self._write_metadata(session, duration_minutes)
        return session

    def _write_metadata(self, session: RecordingSession, duration_minutes: int):
        metadata = session.folder / "metadata.txt"
        metadata.write_text(
            f"recording_id={session.recording_id}\n"
            f"tipo={session.tipo}\n"
            f"titulo={session.titulo}\n"
            f"inicio={session.started_at.isoformat()}\n"
            f"duracao_parte_minutos={duration_minutes}\n",
            encoding="utf-8",
        )

    def _record_part(self, session: RecordingSession, part_number: int):
        part_started_at = self.clock().strftime("%Hh%Mm%Ss")
        file_path = session.folder / f"{part_started_at}_parte{part_number:02d}.opus"

        self._stop_termux_recording()
        self.sleep_fn(1)

        self.bus.publish(
            "recording.part.started",
            "audio",
            str(file_path),
            payload={"recording_id": session.recording_id, "arquivo": str(file_path)},
        )

        self._run_command(
            [
                "termux-microphone-record",
                "-f",
                str(file_path),
                "-l",
                str(session.part_duration_seconds),
            ]
        )

        self._stop_termux_recording()
        self.bus.publish(
            "recording.part.finished",
            "audio",
            str(file_path),
            payload={"recording_id": session.recording_id, "arquivo": str(file_path)},
        )
        return file_path

    def record(self, tipo="Outro", titulo=None, max_parts=None):
        self.running = True
        self.signal_module.signal(self.signal_module.SIGINT, self.stop)
        session = self._build_session(tipo=tipo, titulo=titulo)

        self.bus.publish(
            "recording.started",
            "audio",
            f"Iniciada: {session.folder}",
            payload={"recording_id": session.recording_id, "pasta": str(session.folder)},
        )

        part_number = 1

        try:
            while self.running:
                self._record_part(session, part_number)
                part_number += 1

                if max_parts is not None and part_number > max_parts:
                    self.running = False

            final_status = self.db.get_recording(session.recording_id)
            if final_status and final_status[5] == "interrompida":
                return session.folder

            self.db.update_recording_status(session.recording_id, "finalizada")
            self.bus.publish(
                "recording.completed",
                "audio",
                f"Gravacao finalizada: {session.folder}",
                payload={"recording_id": session.recording_id, "pasta": str(session.folder)},
            )
            return session.folder
        except Exception as exc:
            self.db.update_recording_status(session.recording_id, "erro")
            self.bus.publish(
                "recording.failed",
                "audio",
                str(exc),
                payload={"recording_id": session.recording_id},
            )
            raise
        finally:
            self.active_session = None
