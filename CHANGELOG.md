# Changelog

## v0.3.7
- `AIService` passou a resolver configuracao efetiva para modo `openai` via variaveis de ambiente.
- Suporte a `OPENAI_API_KEY` e sobrescrita de modelo por `OPENAI_MODEL`.
- Fallback claro para `offline` e erro orientado quando `ai.mode=openai` sem chave.

## v0.3.6
- `AIService` offline-first adicionado para gerar resumos da transcricao consolidada mais recente.
- Novo comando `prestes resumir` para gerar resumo por tipo.
- Configuracao preparada para futura integracao com OpenAI sem uso obrigatorio de rede.
- Testes adicionados para fluxo offline de IA e despacho da CLI.

## v0.3.5
- `ConfigService` tornou-se mais robusto com merge de defaults e autocorrecao de configuracao.
- Caminhos principais da configuracao passaram a ser normalizados com `pathlib`.
- Testes adicionados para criacao, merge e validacao do YAML.

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
