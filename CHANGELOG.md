# Changelog

## v0.3.4
- Logs estruturados em JSON por linha adicionados ao `LogService`.
- `EventBus` passou a registrar `source`, `event_type` e `context` no log.
- Testes atualizados para validar o formato estruturado dos logs.

## v0.3.3
- Primeira versao do TranscriptionService adicionada.
- Preparacao da gravacao mais recente para transcricao via `prestes transcrever`.
- Conversao de `.opus`, `.m4a`, `.mp3` e `.wav` para WAV 16 kHz mono com `ffmpeg`.
- Integracao com Whisper.cpp para gerar `TXT`, `SRT`, `JSON` e `TRANSCRICAO_COMPLETA.txt`.
- Persistencia de transcricoes no SQLite quando a gravacao possui `recording_id`.
- Testes adicionados para descoberta da gravacao mais recente, conversao, persistencia e despacho da CLI.

## v0.3.2
- AudioService consolidado com fluxo testavel e tolerancia a falhas.
- Registro de gravacoes no SQLite com atualizacao de status.
- Eventos de audio ampliados para inicio, parte, conclusao, interrupcao e falha.
- CLI passou a aceitar `prestes gravar --tipo ... --titulo ...`.
- Testes adicionados para AudioService, gravacoes no banco e comando direto da CLI.

## v0.3.1
- Integracao do Kit de Governanca ao repositorio.
- Inclusao de `AGENTS.md`, `MASTER_SPEC.md`, `README_GOVERNANCE.md` e da pasta `.ai/`.
- README atualizado com fluxo oficial de desenvolvimento.
- ROADMAP e TASKS alinhados com a governanca atual.
- Testes iniciais adicionados para DatabaseService, LogService, EventBus e smoke test da CLI.
- Servicos principais preparados para testes isolados com caminhos configuraveis.

## v0.3.0
- Starter Kit inicial criado.
- Estrutura profissional Python.
- Core, servicos, documentacao e tarefas para Codex.
