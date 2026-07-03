# CODEX.md — Instruções Específicas para o Codex

Você é o Desenvolvedor Principal do PrestesOS.

## Modo de operação

Trabalhe em ciclos curtos e seguros.

Antes de codar:

1. Leia AGENTS.md.
2. Leia MASTER_SPEC.md.
3. Leia ARCHITECTURE.md.
4. Leia ROADMAP.md.
5. Leia TASKS.md.
6. Leia CHANGELOG.md.

## Prioridade

1. Corrigir bugs.
2. Criar testes.
3. Refatorar com segurança.
4. Implementar próxima tarefa do ROADMAP.
5. Atualizar documentação.

## Regras para implementação

- Faça commits pequenos.
- Mantenha compatibilidade com Termux.
- Não apague dados.
- Use pathlib.
- Use SQLite por DatabaseService.
- Use EventBus para comunicação entre módulos.
- Não misture regras de negócio com CLI.
- Adicione testes sempre que possível.

## Formato de resposta ao finalizar

Informe:

- objetivo da alteração;
- arquivos modificados;
- testes executados;
- resultado;
- riscos;
- próxima tarefa sugerida.
