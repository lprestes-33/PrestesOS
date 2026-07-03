# PrestesOS Starter Kit v0.3

PrestesOS e uma plataforma pessoal de conhecimento, automacao e IA, projetada para funcionar primeiro no Termux e manter compatibilidade com Linux.

## Objetivo inicial

- gravar audio em partes de 30 minutos;
- transcrever com Whisper.cpp;
- organizar arquivos por data e tipo;
- registrar eventos em SQLite;
- preparar integracao com IA, Google Drive e busca semantica.

## Instalacao no Termux

```bash
pkg update -y
pkg install python ffmpeg termux-api git -y
pip install -e .
```

## Executar

Menu interativo:

```bash
prestes
```

Gravacao direta:

```bash
prestes gravar --tipo Aula --titulo "Direito Constitucional"
```

Preparacao da gravacao mais recente para transcricao:

```bash
prestes transcrever
```

Resumo offline da transcricao mais recente:

```bash
prestes resumir --tipo Aula
```

Busca textual local:

```bash
prestes buscar competencia
```

Busca semantica local:

```bash
prestes buscar-semantico jurisdicao
```

Preparacao de sincronizacao local:

```bash
prestes sincronizar
```

Sincronizacao real com Google Drive:

```bash
export GOOGLE_DRIVE_ACCESS_TOKEN="seu_token"
prestes sincronizar
```

## Estrutura

```text
src/prestes_os/
|-- audio/
|-- core/
|-- plugins/
`-- services/
```

## Fluxo de desenvolvimento

Antes de alterar o projeto, leia nesta ordem:

1. `AGENTS.md`
2. `MASTER_SPEC.md`
3. `ARCHITECTURE.md`
4. `ROADMAP.md`
5. `TASKS.md`
6. `CHANGELOG.md`
7. `docs/adr/`
8. `.ai/CODEX.md` ou `.ai/CHATGPT.md`

## Regras essenciais

- Toda comunicacao entre modulos deve passar pelo Prestes Kernel, preferencialmente via EventBus.
- Services concentram regra de negocio.
- CLI/TUI apenas aciona services.
- Toda alteracao relevante deve incluir testes, documentacao e atualizacao do changelog.

## Estado atual dos logs

- cada operacao relevante gera uma linha JSON no arquivo `prestes.log`;
- os campos padrao incluem `timestamp`, `level`, `message`, `source`, `event_type` e `context`;
- eventos publicados no `EventBus` tambem sao refletidos no log estruturado.

## Estado atual da configuracao

- a configuracao continua centralizada em `config/config.yaml`;
- chaves ausentes sao recompostas automaticamente a partir dos defaults;
- caminhos principais sao normalizados com `pathlib`;
- valores criticos invalidos sao corrigidos para defaults seguros.

## Estado atual do audio

- cria pasta por data no formato `ddmmaaaa`;
- gera `metadata.txt` da sessao;
- registra gravacao no SQLite;
- publica eventos de inicio, parte, conclusao e falha;
- suporta comando direto `prestes gravar`.

## Estado atual da transcricao

- localiza a pasta de gravacao mais recente;
- seleciona arquivos `.opus`, `.m4a`, `.mp3` e `.wav`;
- converte cada arquivo para WAV 16 kHz mono via `ffmpeg`;
- executa Whisper.cpp por arquivo WAV;
- gera `TXT`, `SRT`, `JSON` e `TRANSCRICAO_COMPLETA.txt`;
- registra textos no SQLite quando `recording_id` estiver presente no `metadata.txt`;
- publica eventos de preparacao, conversao e transcricao;
- suporta comando direto `prestes transcrever`.

## Estado atual da IA

- existe `AIService` em modo `offline`;
- consome a transcricao consolidada mais recente;
- detecta o tipo pelo `metadata.txt` ou aceita tipo explicito;
- gera resumo em arquivo na pasta `Resumos`;
- possui preparacao para modo `openai` por variavel de ambiente;
- usa `OPENAI_API_KEY` e pode sobrescrever modelo via `OPENAI_MODEL`.

## Estado atual da busca

- existe busca textual local em SQLite;
- transcricoes consolidadas e resumos podem ser indexados;
- a indexacao ocorre por arquivo e preserva caminho e tipo da fonte;
- a CLI suporta busca direta com `prestes buscar`;
- existe busca semantica offline leve com expansao local de conceitos.

## Estado atual da sincronizacao

- existe `SyncService` em modo local-first;
- o sistema gera manifesto JSON com arquivos preparados para sincronizacao;
- transcricoes e resumos entram no manifesto automaticamente;
- existe modo preparatorio para Google Drive com plano de upload e pasta remota configuravel;
- o upload real pode ocorrer pela API do Google Drive quando `sync.provider=google-drive`;
- o estado de sincronizacao e persistido localmente para evitar reenvio de arquivos inalterados;
- o token de acesso e lido por variavel de ambiente para evitar segredo no YAML.

## Proximo objetivo

O desenvolvimento deve continuar a partir de `TASKS.md`, respeitando a ordem de prioridades definida em `AGENTS.md`.
