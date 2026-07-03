from datetime import datetime

from prestes_os.audio.audio_service import AudioService
from prestes_os.services.config_service import ConfigService
from prestes_os.services.event_bus import EventBus


class FakeSignalModule:
    SIGINT = object()

    def __init__(self):
        self.handlers = []

    def signal(self, sig, handler):
        self.handlers.append((sig, handler))


def build_audio_service(prestes_base_dir, database_service, log_service, monkeypatch, command_runner):
    config = ConfigService(base_dir=prestes_base_dir)
    bus = EventBus(db_service=database_service, log_service=log_service)
    signal_module = FakeSignalModule()
    timestamps = iter(
        [
            datetime(2026, 1, 2, 8, 30, 0),
            datetime(2026, 1, 2, 8, 30, 0),
            datetime(2026, 1, 2, 9, 0, 0),
            datetime(2026, 1, 2, 9, 30, 0),
        ]
    )

    service = AudioService(
        config_service=config,
        event_bus=bus,
        database_service=database_service,
        command_runner=command_runner,
        sleep_fn=lambda *_: None,
        signal_module=signal_module,
        clock=lambda: next(timestamps),
    )
    monkeypatch.setattr(service, "_stop_termux_recording", lambda: command_runner(["termux-microphone-record", "-q"]))
    return service


def test_audio_service_creates_folder_metadata_and_db_record(
    prestes_base_dir, database_service, log_service, monkeypatch
):
    commands = []

    def command_runner(args, **kwargs):
        commands.append(args)
        return None

    service = build_audio_service(
        prestes_base_dir,
        database_service,
        log_service,
        monkeypatch,
        command_runner,
    )

    folder = service.record(tipo="Aula", titulo="Introducao ao Processo", max_parts=1)
    row = database_service.get_recording(1)
    metadata = (folder / "metadata.txt").read_text(encoding="utf-8")

    assert folder.exists()
    assert "recording_id=1" in metadata
    assert "titulo=Introducao ao Processo" in metadata
    assert row is not None
    assert row[2] == "Introducao ao Processo"
    assert row[5] == "finalizada"
    assert ["termux-microphone-record", "-f", str(folder / "08h30m00s_parte01.opus"), "-l", "1800"] in commands


def test_audio_service_marks_recording_as_error_on_failure(
    prestes_base_dir, database_service, log_service, monkeypatch
):
    def command_runner(args, **kwargs):
        if "-f" in args:
            raise RuntimeError("falha simulada")
        return None

    service = build_audio_service(
        prestes_base_dir,
        database_service,
        log_service,
        monkeypatch,
        command_runner,
    )

    try:
        service.record(tipo="Reuniao", titulo="Status", max_parts=1)
    except RuntimeError as exc:
        assert "falha simulada" in str(exc)
    else:
        raise AssertionError("Era esperado propagar a falha da gravacao.")

    row = database_service.get_recording(1)
    events = database_service.last_events(5)

    assert row[5] == "erro"
    assert any(event[1] == "recording.failed" for event in events)
