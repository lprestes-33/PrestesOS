# ARCHITECT.md — Conselho de Arquitetura

## Princípios

- Baixo acoplamento.
- Alta coesão.
- Modularidade.
- Testabilidade.
- Observabilidade.
- Offline-first.
- Compatibilidade com Termux.

## Decisões permanentes

- Prestes Kernel coordena o sistema.
- EventBus é o mecanismo padrão de comunicação.
- Services contêm regra de negócio.
- Plugins não dependem diretamente uns dos outros.
- SQLite é persistência local padrão.
- Configuração fica em YAML.
- Logs são obrigatórios para ações relevantes.

## Quando criar ADR

Crie ADR ao:

- adicionar dependência relevante;
- mudar arquitetura;
- alterar banco de dados;
- criar novo serviço;
- criar novo plugin;
- mudar fluxo central.
