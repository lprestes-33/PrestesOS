# MASTER_SPEC.md — Constituição Técnica do PrestesOS

O PrestesOS é uma plataforma pessoal de conhecimento, automação e IA.

## Objetivo

Capturar, organizar, compreender e recuperar informações de forma modular, segura e pesquisável.

## Arquitetura

- Prestes Kernel
- Services
- Plugins
- EventBus
- SQLite
- Logs
- Configuração YAML
- IA desacoplada
- Sincronização opcional

## Regra central

Nenhuma funcionalidade deve ser implementada como script isolado quando puder ser modelada como serviço ou plugin.

## Compatibilidade

O ambiente principal é Termux/Android, mantendo compatibilidade com Linux sempre que possível.
