# Arquitetura PrestesOS

## Decisão central

O PrestesOS é uma plataforma modular em Python, com núcleo mínimo e serviços desacoplados.

## Camadas

```text
CLI / Menu
   ↓
Prestes Kernel
   ↓
Services
   ↓
Plugins
   ↓
Storage / IA / Arquivos
```

## Serviços principais

- ConfigService
- LogService
- DatabaseService
- EventBus
- AudioService
- AIService
- SyncService

## Princípios

1. Nenhum dado original deve ser apagado automaticamente.
2. Toda ação importante gera log.
3. Todo arquivo processado deve ter metadados.
4. Módulos não devem depender diretamente uns dos outros.
5. Comunicação entre módulos deve ocorrer por eventos.
