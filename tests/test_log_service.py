def test_log_service_writes_formatted_line(log_service):
    log_service.info("mensagem de teste")

    content = log_service.log_file.read_text(encoding="utf-8")

    assert "[INFO] mensagem de teste" in content
