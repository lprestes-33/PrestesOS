# AGENTS.md — Regras Gerais para Agentes de IA no PrestesOS

Este arquivo é o ponto de entrada obrigatório para qualquer agente de IA que trabalhe no PrestesOS.

## Ordem obrigatória de leitura

Antes de alterar qualquer arquivo, leia:

1. README.md
2. MASTER_SPEC.md
3. ARCHITECTURE.md
4. ROADMAP.md
5. TASKS.md
6. CHANGELOG.md
7. docs/adr/
8. .ai/CODEX.md ou .ai/CHATGPT.md, conforme o agente utilizado

## Fonte da verdade

Em caso de conflito entre documentos, siga esta ordem:

1. MASTER_SPEC.md
2. ARCHITECTURE.md
3. AGENTS.md
4. ROADMAP.md
5. TASKS.md
6. README.md

## Missão dos agentes

Evoluir o PrestesOS como uma plataforma modular, estável, testável, documentada e compatível com Termux/Linux.

## Regras obrigatórias

Nunca:

- apagar dados do usuário;
- quebrar compatibilidade com Termux sem justificativa;
- remover funcionalidades existentes sem motivo técnico;
- acessar SQLite diretamente quando existir serviço apropriado;
- introduzir dependências pesadas sem justificativa;
- alterar arquitetura sem registrar ADR.

Sempre:

- preservar modularidade;
- usar pathlib;
- registrar logs e eventos;
- tratar exceções;
- criar ou atualizar testes;
- atualizar documentação;
- atualizar CHANGELOG;
- fazer commits pequenos e descritivos.

## Fluxo de trabalho

Para cada tarefa:

1. Analise o estado atual.
2. Identifique a prioridade.
3. Explique o plano.
4. Implemente uma tarefa por vez.
5. Teste.
6. Corrija falhas.
7. Atualize documentação.
8. Atualize CHANGELOG.
9. Sugira próximo passo.

## Arquitetura obrigatória

Toda comunicação entre módulos deve ocorrer pelo Prestes Kernel, preferencialmente via EventBus.

Services concentram lógica de negócio.

Plugins implementam domínios específicos.

Commands/CLI apenas acionam serviços.
