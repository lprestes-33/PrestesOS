from prestes_os.services.event_bus import EventBus


def test_event_bus_persists_event_and_notifies_listener(database_service, log_service):
    payloads = []

    bus = EventBus(db_service=database_service, log_service=log_service)
    bus.subscribe("recording.started", payloads.append)

    bus.publish(
        "recording.started",
        origem="audio",
        descricao="gravacao iniciada",
        payload={"arquivo": "teste.opus"},
    )

    rows = database_service.last_events(1)

    assert payloads == [{"arquivo": "teste.opus"}]
    assert rows[0][1] == "recording.started"
    assert rows[0][2] == "audio"
    assert rows[0][3] == "gravacao iniciada"
    log_line = log_service.log_file.read_text(encoding="utf-8").strip()
    assert '"event_type": "recording.started"' in log_line
    assert '"source": "audio"' in log_line
