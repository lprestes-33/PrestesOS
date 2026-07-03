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

## Proximo objetivo

O desenvolvimento deve continuar a partir de `TASKS.md`, respeitando a ordem de prioridades definida em `AGENTS.md`.
