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


def test_database_persists_transcription(database_service):
    transcription_id = database_service.create_transcription(
        gravacao_id=7,
        arquivo="parte01.txt",
        texto="texto consolidado",
    )

    rows = database_service.list_transcriptions(7)

    assert transcription_id > 0
    assert len(rows) == 1
    assert rows[0][2] == "parte01.txt"
    assert rows[0][3] == "texto consolidado"


def test_database_upserts_search_document(database_service):
    database_service.upsert_search_document(
        source_type="summary",
        source_path="C:/tmp/resumo.txt",
        title="Resumo: aula-processo",
        content="processo civil e competencia",
        metadata="folder=aula-processo",
    )
    database_service.upsert_search_document(
        source_type="summary",
        source_path="C:/tmp/resumo.txt",
        title="Resumo: aula-processo",
        content="processo civil atualizado",
        metadata="folder=aula-processo",
    )

    rows = database_service.search_documents("atualizado")

    assert len(rows) == 1
    assert rows[0][1] == "summary"
    assert rows[0][4] == "processo civil atualizado"
