def test_database_initializes(database_service):
    database_service.add_event("test.event", "pytest", "evento de teste")

    rows = database_service.last_events(1)

    assert rows
    assert rows[0][1] == "test.event"
