import json


def test_log_service_writes_structured_line(log_service):
    log_service.info(
        "mensagem de teste",
        source="pytest",
        event_type="teste.executado",
        context={"resultado": "ok"},
    )

    line = log_service.log_file.read_text(encoding="utf-8").strip()
    payload = json.loads(line)

    assert payload["level"] == "INFO"
    assert payload["message"] == "mensagem de teste"
    assert payload["source"] == "pytest"
    assert payload["event_type"] == "teste.executado"
    assert payload["context"]["resultado"] == "ok"
