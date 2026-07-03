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
    (latest / "metadata.txt").write_text("recording_id=42\nmeta=ok\n", encoding="utf-8")
    return older, latest


def build_service(prestes_base_dir, database_service, log_service, ffmpeg_runner, whisper_runner):
    config = ConfigService(base_dir=prestes_base_dir)
    data = config.load()
    model_path = prestes_base_dir / "models" / "ggml-small.bin"
    model_path.parent.mkdir(parents=True, exist_ok=True)
    model_path.write_bytes(b"model")
    data["audio"]["modelo_whisper"] = str(model_path)
    data["audio"]["comando_whisper"] = "whisper-cli"
    config.save(data)

    bus = EventBus(db_service=database_service, log_service=log_service)
    return TranscriptionService(
        config_service=config,
        event_bus=bus,
        database_service=database_service,
        ffmpeg_runner=ffmpeg_runner,
        whisper_runner=whisper_runner,
    )


def test_transcription_service_detects_latest_recording_folder(
    prestes_base_dir, database_service, log_service
):
    older, latest = create_recording_fixture(prestes_base_dir)
    latest.touch()
    older.touch()

    service = build_service(
        prestes_base_dir,
        database_service,
        log_service,
        ffmpeg_runner=lambda *args, **kwargs: None,
        whisper_runner=lambda *args, **kwargs: None,
    )

    result = service.find_latest_recording_folder()

    assert result == latest


def test_transcription_service_prepares_wav_files(prestes_base_dir, database_service, log_service):
    _, latest = create_recording_fixture(prestes_base_dir)
    commands = []

    def ffmpeg_runner(args, **kwargs):
        commands.append(args)
        output_path = Path(args[-1])
        output_path.write_bytes(b"wav")
        return None

    service = build_service(
        prestes_base_dir,
        database_service,
        log_service,
        ffmpeg_runner=ffmpeg_runner,
        whisper_runner=lambda *args, **kwargs: None,
    )

    result = service.prepare_latest_recording()
    events = database_service.last_events(5)

    assert result.source_folder == latest
    assert result.output_folder.exists()
    assert [path.name for path in result.converted_files] == ["parte01.wav", "parte02.wav"]
    assert any(event[1] == "transcription.preparation.completed" for event in events)
    assert commands[0][:6] == ["ffmpeg", "-y", "-i", str(latest / "parte01.opus"), "-ar", "16000"]
    assert commands[1][:6] == ["ffmpeg", "-y", "-i", str(latest / "parte02.mp3"), "-ar", "16000"]


def test_transcription_service_transcribes_and_persists_outputs(
    prestes_base_dir, database_service, log_service
):
    _, latest = create_recording_fixture(prestes_base_dir)

    def ffmpeg_runner(args, **kwargs):
        output_path = Path(args[-1])
        output_path.write_bytes(b"wav")
        return None

    def whisper_runner(args, **kwargs):
        output_base = Path(args[-1])
        stem = output_base.name
        output_base.with_suffix(".txt").write_text(f"texto {stem}", encoding="utf-8")
        output_base.with_suffix(".srt").write_text(f"srt {stem}", encoding="utf-8")
        output_base.with_suffix(".json").write_text(f'{{"text":"texto {stem}"}}', encoding="utf-8")
        return None

    service = build_service(
        prestes_base_dir,
        database_service,
        log_service,
        ffmpeg_runner=ffmpeg_runner,
        whisper_runner=whisper_runner,
    )

    result = service.transcribe_latest_recording()
    events = database_service.last_events(10)
    rows = database_service.list_transcriptions(42)

    assert result.source_folder == latest
    assert result.recording_id == 42
    assert result.consolidated_file.exists()
    assert "texto parte01" in result.consolidated_file.read_text(encoding="utf-8")
    assert "texto parte02" in result.consolidated_file.read_text(encoding="utf-8")
    assert len(result.artifacts) == 2
    assert len(rows) == 2
    assert rows[0][2].endswith("parte01.txt")
    assert any(event[1] == "transcription.completed" for event in events)


def test_transcription_service_fails_without_supported_audio_files(
    prestes_base_dir, database_service, log_service
):
    folder = prestes_base_dir / "Gravacoes" / "02012026" / "vazia"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "metadata.txt").write_text("meta", encoding="utf-8")

    service = build_service(
        prestes_base_dir,
        database_service,
        log_service,
        ffmpeg_runner=lambda *args, **kwargs: None,
        whisper_runner=lambda *args, **kwargs: None,
    )

    try:
        service.list_supported_audio_files(folder)
    except FileNotFoundError as exc:
        assert "Nenhum arquivo de audio suportado" in str(exc)
    else:
        raise AssertionError("Era esperado falhar sem arquivos suportados.")
