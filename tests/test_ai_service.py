from pathlib import Path

from prestes_os.services.ai_service import AIService
from prestes_os.services.config_service import ConfigService
from prestes_os.services.event_bus import EventBus


def create_ai_fixture(prestes_base_dir: Path) -> Path:
    recording_folder = prestes_base_dir / "Gravacoes" / "03072026" / "aula-processo"
    recording_folder.mkdir(parents=True, exist_ok=True)
    (recording_folder / "metadata.txt").write_text("tipo=Aula\nrecording_id=9\n", encoding="utf-8")

    transcription_folder = prestes_base_dir / "Transcricoes" / "03072026" / "aula-processo"
    transcription_folder.mkdir(parents=True, exist_ok=True)
    consolidated = transcription_folder / "TRANSCRICAO_COMPLETA.txt"
    consolidated.write_text(
        "Processo civil trata da relacao juridica. A competencia organiza o julgamento. "
        "As partes precisam compreender os atos processuais.",
        encoding="utf-8",
    )
    return consolidated


def test_ai_service_generates_offline_summary(prestes_base_dir, database_service, log_service):
    consolidated = create_ai_fixture(prestes_base_dir)
    config = ConfigService(base_dir=prestes_base_dir)
    bus = EventBus(db_service=database_service, log_service=log_service)
    service = AIService(config_service=config, event_bus=bus)

    result = service.summarize_latest_transcription()
    events = database_service.last_events(5)

    assert result.source_file == consolidated
    assert result.summary_type == "Aula"
    assert result.output_file.exists()
    assert "Resumo de Aula" in result.content
    assert any(event[1] == "ai.summary.completed" for event in events)


def test_ai_service_respects_explicit_summary_type(prestes_base_dir, database_service, log_service):
    create_ai_fixture(prestes_base_dir)
    config = ConfigService(base_dir=prestes_base_dir)
    bus = EventBus(db_service=database_service, log_service=log_service)
    service = AIService(config_service=config, event_bus=bus)

    result = service.summarize_latest_transcription(summary_type="Reuniao")

    assert result.summary_type == "Reuniao"
    assert "Ata de Reuniao" in result.content


def test_ai_service_blocks_unimplemented_online_mode(prestes_base_dir, database_service, log_service):
    create_ai_fixture(prestes_base_dir)
    config = ConfigService(base_dir=prestes_base_dir)
    data = config.load()
    data["ai"]["mode"] = "openai"
    config.save(data)
    bus = EventBus(db_service=database_service, log_service=log_service)
    service = AIService(config_service=config, event_bus=bus)

    try:
        service.summarize_latest_transcription()
    except RuntimeError as exc:
        assert "Modo online ainda nao implementado" in str(exc)
    else:
        raise AssertionError("Era esperado falhar em modo openai placeholder.")
