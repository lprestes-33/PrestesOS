from pathlib import Path

from prestes_os.services.config_service import ConfigService
from prestes_os.services.event_bus import EventBus
from prestes_os.services.transcription_service import TranscriptionService


def create_recording_fixture(prestes_base_dir: Path) -> tuple[Path, Path]:
    recordings_root = prestes_base_dir / "Gravacoes"
    older = recordings_root / "01012026" / "aula-antiga"
    latest = recordings_root / "02012026" / "reuniao-recente"
    older.mkdir(parents=True, exist_ok=True)
    latest.mkdir(parents=True, exist_ok=True)
    (older / "parte01.opus").write_text("old", encoding="utf-8")
    (latest / "parte01.opus").write_text("new", encoding="utf-8")
    (latest / "parte02.mp3").write_text("new2", encoding="utf-8")
    (latest / "metadata.txt").write_text("meta", encoding="utf-8")
    return older, latest


def test_transcription_service_detects_latest_recording_folder(
    prestes_base_dir, database_service, log_service
):
    older, latest = create_recording_fixture(prestes_base_dir)
    latest.touch()
    older.touch()

    config = ConfigService(base_dir=prestes_base_dir)
    bus = EventBus(db_service=database_service, log_service=log_service)
    service = TranscriptionService(config_service=config, event_bus=bus, command_runner=lambda *args, **kwargs: None)

    result = service.find_latest_recording_folder()

    assert result == latest


def test_transcription_service_prepares_wav_files(prestes_base_dir, database_service, log_service):
    _, latest = create_recording_fixture(prestes_base_dir)
    commands = []

    def command_runner(args, **kwargs):
        commands.append(args)
        output_path = Path(args[-1])
        output_path.write_bytes(b"wav")
        return None

    config = ConfigService(base_dir=prestes_base_dir)
    bus = EventBus(db_service=database_service, log_service=log_service)
    service = TranscriptionService(config_service=config, event_bus=bus, command_runner=command_runner)

    result = service.prepare_latest_recording()
    events = database_service.last_events(5)

    assert result.source_folder == latest
    assert result.output_folder.exists()
    assert [path.name for path in result.converted_files] == ["parte01.wav", "parte02.wav"]
    assert any(event[1] == "transcription.preparation.completed" for event in events)
    assert commands[0][:6] == ["ffmpeg", "-y", "-i", str(latest / "parte01.opus"), "-ar", "16000"]
    assert commands[1][:6] == ["ffmpeg", "-y", "-i", str(latest / "parte02.mp3"), "-ar", "16000"]


def test_transcription_service_fails_without_supported_audio_files(
    prestes_base_dir, database_service, log_service
):
    folder = prestes_base_dir / "Gravacoes" / "02012026" / "vazia"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "metadata.txt").write_text("meta", encoding="utf-8")

    config = ConfigService(base_dir=prestes_base_dir)
    bus = EventBus(db_service=database_service, log_service=log_service)
    service = TranscriptionService(config_service=config, event_bus=bus, command_runner=lambda *args, **kwargs: None)

    try:
        service.list_supported_audio_files(folder)
    except FileNotFoundError as exc:
        assert "Nenhum arquivo de audio suportado" in str(exc)
    else:
        raise AssertionError("Era esperado falhar sem arquivos suportados.")
