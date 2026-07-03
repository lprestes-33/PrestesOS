def test_database_initializes(database_service):
    database_service.add_event("test.event", "pytest", "evento de teste")

    rows = database_service.last_events(1)

    assert rows
    assert rows[0][1] == "test.event"


def test_database_persists_recording(database_service, prestes_base_dir):
    recording_id = database_service.create_recording(
        tipo="Aula",
        titulo="Aula de Processo Civil",
        pasta=prestes_base_dir / "Gravacoes" / "01012026" / "aula",
        status="gravando",
    )
    database_service.update_recording_status(recording_id, "finalizada")

    row = database_service.get_recording(recording_id)

    assert row is not None
    assert row[1] == "Aula"
    assert row[2] == "Aula de Processo Civil"
    assert row[5] == "finalizada"
