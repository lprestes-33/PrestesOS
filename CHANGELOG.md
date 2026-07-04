# Changelog

## v0.3.22
- Novo comando `prestes proximo-ciclo` para exibir o planejamento priorizado do ciclo pos-v1.0.
- `PlanningService` adicionado para transformar o roadmap futuro em um plano consultavel pela plataforma.
- Menu interativo atualizado com acesso direto ao proximo ciclo.
- Testes adicionados para o planejamento e para o despacho da CLI.

## v0.3.21
- Novo comando `prestes status` para diagnostico consolidado da plataforma visando o fechamento operacional da v1.0.
- `PlatformService` adicionado para resumir configuracao, banco, logs, sync e integracoes preparatorias.
- Contadores simples adicionados ao `DatabaseService` para apoiar diagnosticos locais.
- Testes adicionados para o diagnostico consolidado e para o despacho da CLI.

## v0.3.20
- `NotebookLMService` adicionado para preparar autenticacao e configuracao da futura integracao com NotebookLM.
- Novo comando `prestes notebooklm-status` para diagnostico local da integracao.
- Configuracao `notebooklm` adicionada ao YAML com token por ambiente ou arquivo local.
- Testes adicionados para autenticacao NotebookLM e despacho da CLI.

## v0.3.19
- `CalendarService` adicionado para preparar autenticacao e configuracao da futura integracao com Google Calendar.
- Novo comando `prestes calendar-status` para diagnostico local da integracao.
- Configuracao `calendar` adicionada ao YAML com token por ambiente ou arquivo local.
- Testes adicionados para autenticacao Calendar e despacho da CLI.

## v0.3.18
- `GmailService` adicionado para preparar autenticacao e configuracao da futura integracao com Gmail.
- Novo comando `prestes gmail-status` para diagnostico local da integracao.
- Configuracao `gmail` adicionada ao YAML com token por ambiente ou arquivo local.
- Testes adicionados para autenticacao Gmail e despacho da CLI.

## v0.3.17
- Autenticacao Google Drive melhorada com suporte a token por arquivo local ou variavel de ambiente.
- Tokens em arquivo agora podem informar expiracao e sao validados antes do upload.
- CLI de sincronizacao passou a informar a origem efetiva da autenticacao.
- Testes adicionados para autenticacao por arquivo e token expirado.

## v0.3.16
- Novo comando `prestes resumo-sync` para exibir resumos por execucao de sincronizacao.
- `SyncService` passou a persistir resumos de lote com identificador, contagens e data.
- A execucao de sincronizacao agora informa `run_id` para auditoria local.
- Testes adicionados para resumo de execucao e despacho da CLI.

## v0.3.15
- Novo comando `prestes falhas-sync` para exibir falhas recentes de sincronizacao.
- `SyncService` passou a persistir falhas locais de upload em arquivo JSON dedicado.
- Falhas por arquivo nao interrompem os demais uploads do mesmo lote.
- Testes adicionados para registro de falhas e despacho da CLI.

## v0.3.14
- Novo comando `prestes historico-sync` para exibir o historico local de sincronizacao.
- `SyncService` passou a expor leitura estruturada do estado incremental persistido.
- Menu interativo ganhou acesso ao historico de sincronizacao.
- Testes adicionados para leitura do historico e despacho da CLI.

## v0.3.13
- Estado incremental de sincronizacao adicionado em arquivo local JSON.
- `SyncService` passou a ignorar arquivos ja enviados sem alteracao de hash ou destino remoto.
- CLI de sincronizacao passou a informar arquivos ignorados e reaproveitados.
- Testes adicionados para persistencia e reaproveitamento de estado em execucoes consecutivas.

## v0.3.12
- Upload real para Google Drive adicionado via API HTTP com token Bearer em variavel de ambiente.
- `SyncService` passou a executar sincronizacao completa quando `sync.provider=google-drive`.
- Cliente leve de Google Drive adicionado sem dependencias externas pesadas.
- Testes adicionados para upload pendente por autenticacao e envio remoto com cliente simulado.

## v0.3.11
- `SyncService` passou a preparar plano de upload para Google Drive sem acoplamento com rede.
- Configuracao de `sync.google_drive` adicionada com pasta remota, credenciais e arquivo de plano.
- CLI de sincronizacao passou a informar o plano Google Drive e o estado das credenciais.
- Testes adicionados para plano Google Drive com e sem credenciais.

## v0.3.10
- `SyncService` adicionado para gerar manifesto local de sincronizacao.
- Novo comando `prestes sincronizar`.
- Testes adicionados para manifesto, logs opcionais e despacho da CLI.

## v0.3.9
- Busca semantica offline inicial adicionada ao `SearchService`.
- Novo comando `prestes buscar-semantico` para consulta conceitual local.
- Testes adicionados para busca semantica e despacho da CLI.

## v0.3.8
- `SearchService` adicionado para indexacao e busca textual local em SQLite.
- Novo comando `prestes buscar` para consulta textual em transcricoes e resumos.
- Testes adicionados para indexacao, busca e despacho da CLI.

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
